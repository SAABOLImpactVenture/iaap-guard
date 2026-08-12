from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Iterable

from .loader import IGNORED_DIRS, MAX_FILE_BYTES, SUPPORTED_SUFFIXES, load_artifacts
from .product import load_product_manifest

MANIFEST_PATH = ".iaap/product.yaml"
STATUS_ORDER = {"BLOCKED": 0, "ADVISORY": 1, "READY": 2, "NOT_APPLICABLE": 3}


def requirement(
    requirement_id: str,
    name: str,
    status: str,
    observed: str,
    impact: str,
    remediation: str,
    *,
    severity: str = "blocking",
    repository: str | None = None,
    path: str | None = None,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "id": requirement_id,
        "name": name,
        "status": status,
        "severity": severity,
        "blocking": status == "BLOCKED" and severity == "blocking",
        "observed": observed,
        "impact": impact,
        "remediation": remediation,
    }
    if repository is not None:
        item["repository"] = repository
    if path is not None:
        item["path"] = path
    return item


def build_readiness_report(
    mode: str,
    repository: str | None,
    product: dict[str, Any] | None,
    requirements: Iterable[dict[str, Any]],
    members: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    ordered = sorted(requirements, key=lambda item: (item["id"], item.get("repository", ""), item.get("path", "")))
    blocking = [item["id"] for item in ordered if item["blocking"]]
    advisory = [item["id"] for item in ordered if item["status"] == "ADVISORY"]
    overall = "BLOCKED" if blocking else "READY_WITH_ADVISORIES" if advisory else "READY"
    report: dict[str, Any] = {
        "schemaVersion": "readiness-report/v1",
        "scope": {"mode": mode},
        "overallStatus": overall,
        "summary": {
            "total": len(ordered),
            "ready": sum(item["status"] == "READY" for item in ordered),
            "advisory": len(advisory),
            "blocked": len(blocking),
            "notApplicable": sum(item["status"] == "NOT_APPLICABLE" for item in ordered),
        },
        "requirements": ordered,
        "blockingRequirements": blocking,
        "advisoryRequirements": advisory,
        "productMembers": sorted(members or [], key=lambda item: item["repository"]),
        "boundary": {
            "diagnosticOnly": True,
            "architectureCheckConclusionUnchanged": True,
            "doesNotExpandGitHubAppPermissions": True,
            "localNetworkAccess": False,
            "evidenceContinuitySemanticsUnchanged": True,
            "productAssessmentSemanticsUnchanged": True,
        },
    }
    if repository is not None:
        report["repository"] = {"name": repository}
    if product is not None:
        report["product"] = {"id": product["id"], "name": product["name"], "owner": product.get("owner")}
    return report


def evaluate_repository_readiness(target: str | Path, *, repository: str | None = None) -> dict[str, Any]:
    root = Path(target).resolve()
    repo_name = repository or (root.name if root.is_dir() else root.parent.name)
    requirements: list[dict[str, Any]] = []
    if not root.exists() or not os.access(root, os.R_OK):
        requirements.append(requirement("IAP-RDY001", "Repository path", "BLOCKED", f"{root} does not exist or is not readable.", "Guard cannot inspect repository evidence.", "Provide an existing readable repository path.", repository=repo_name, path=str(root)))
        return build_readiness_report("repository", repo_name, None, requirements)
    requirements.append(requirement("IAP-RDY001", "Repository path", "READY", f"{root} exists and is readable.", "Guard can inspect local evidence.", "No action required.", repository=repo_name, path=str(root)))

    candidates: list[Path] = []
    oversized: list[str] = []
    paths = [root] if root.is_file() else sorted(root.rglob("*"))
    base = root if root.is_dir() else root.parent
    for path in paths:
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        relative = path.relative_to(base)
        if any(part in IGNORED_DIRS for part in relative.parts[:-1]):
            continue
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                oversized.append(relative.as_posix())
            else:
                candidates.append(path)
        except OSError:
            oversized.append(relative.as_posix())
    if candidates:
        requirements.append(requirement("IAP-RDY002", "Supported analysis artifacts", "READY", f"Discovered {len(candidates)} supported file(s).", "Guard has bounded files it can analyze.", "No action required.", severity="advisory", repository=repo_name))
    else:
        requirements.append(requirement("IAP-RDY002", "Supported analysis artifacts", "ADVISORY", "No readable supported files were discovered.", "Guard may have too little evidence to produce a meaningful architecture evaluation.", "Add relevant .yaml, .yml, .json, .tf, .tofu, .hcl, .md, .py, or .sh product evidence.", severity="advisory", repository=repo_name))
    requirements.append(requirement("IAP-RDY003", "Per-file analysis bound", "BLOCKED" if oversized else "READY", f"{len(oversized)} supported file(s) exceed the {MAX_FILE_BYTES}-byte analysis bound" + (f": {', '.join(oversized)}" if oversized else "."), "Oversized relevant files are skipped and can make the evaluation incomplete.", "Reduce or split each listed relevant file below the current Guard per-file bound.", repository=repo_name))

    artifacts = load_artifacts(root)
    meaningful = [a for a in artifacts if set(a.contexts) - {"unknown", "documentation-fixture"}]
    requirements.append(requirement("IAP-RDY004", "Recognizable IaaP evidence", "READY" if meaningful else "ADVISORY", f"Recognized IaaP component context in {len(meaningful)} of {len(artifacts)} analyzed artifact(s).", "Recognizable evidence lets Guard apply architecture controls meaningfully." if meaningful else "Guard may return mostly NOT_APPLICABLE because little recognizable IaaP evidence is present.", "No action required." if meaningful else "Add explicit product contracts, experience, control-plane, governance, or validation evidence where applicable.", severity="advisory", repository=repo_name))

    manifest_path = (root if root.is_dir() else root.parent) / MANIFEST_PATH
    product = None
    if not manifest_path.exists():
        requirements.append(requirement("IAP-RDY005", "Multi-repository product registration", "NOT_APPLICABLE", "No .iaap/product.yaml is configured.", "This is normal for a single-repository installation.", "No action required unless this repository is part of a logical product spanning multiple repositories.", severity="advisory", repository=repo_name, path=MANIFEST_PATH))
    else:
        try:
            manifest = load_product_manifest(manifest_path)
            product = manifest["product"]
            requirements.append(requirement("IAP-RDY005", "Product manifest validity", "READY", "The manifest parses and validates as iaap-product/v1.", "The local product boundary is structurally usable.", "No action required.", repository=repo_name, path=MANIFEST_PATH))
            names = [item["name"] for item in manifest["repositories"]]
            if repository is None:
                requirements.append(requirement("IAP-RDY006", "Trigger repository membership", "ADVISORY", "Repository identity was not supplied, so self-membership cannot be confirmed locally.", "GitHub federation requires the triggering repository to register itself.", "Run preflight with --repository owner/name.", severity="advisory", path=MANIFEST_PATH))
            else:
                requirements.append(requirement("IAP-RDY006", "Trigger repository membership", "READY" if repository in names else "BLOCKED", f"{repository} {'is' if repository in names else 'is not'} listed in the product manifest.", "A triggering repository absent from trusted membership cannot safely activate federation.", f"Add {repository} to the identical iaap-product/v1 membership declaration." if repository not in names else "No action required.", repository=repository, path=MANIFEST_PATH))
            requirements.append(requirement("IAP-RDY007", "GitHub product trust and acquisition", "NOT_APPLICABLE", "Local preflight does not evaluate App access, visibility, reciprocal default-branch manifests, immutable SHAs, or evidence acquisition.", "Those checks determine whether registered federation can complete at runtime, but do not block local registration readiness.", "Run the GitHub-aware App preflight when the registered product is evaluated by GitHub; no credentials are required for this local command.", severity="advisory", repository=repo_name, path=MANIFEST_PATH))
        except (OSError, ValueError) as exc:
            requirements.append(requirement("IAP-RDY005", "Product manifest validity", "BLOCKED", str(exc), "Malformed registration prevents Guard from establishing a trusted product boundary.", "Correct .iaap/product.yaml to satisfy the existing iaap-product/v1 contract.", repository=repo_name, path=MANIFEST_PATH))
    return build_readiness_report("product" if product else "repository", repo_name, product, requirements)


def render_readiness_markdown(report: dict[str, Any]) -> str:
    mode = report["scope"]["mode"]
    lines = ["# IaaP Guard Adoption Readiness", "", f"Repository mode: **{report['overallStatus']}**"]
    if mode == "repository" and any(item["id"] == "IAP-RDY005" and item["status"] == "NOT_APPLICABLE" for item in report["requirements"]):
        lines += ["Multi-repository product registration: **NOT CONFIGURED**", "No action required unless this repository is part of a logical product spanning multiple repositories."]
    lines += ["", "## Requirements", ""]
    for item in report["requirements"]:
        lines += [f"### {item['id']} — {item['name']}: {item['status']}", "", f"Observed: {item['observed']}", "", f"Impact: {item['impact']}", "", f"Remediation: {item['remediation']}", ""]
    lines += ["> Readiness is diagnostic only. Architecture Check conclusions, Evidence Continuity, and Product Assessment retain their existing semantics."]
    return "\n".join(lines).rstrip() + "\n"
