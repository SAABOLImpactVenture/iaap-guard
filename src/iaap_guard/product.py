from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

MAX_PRODUCT_REPOSITORIES = 12

ROLE_ORDER = (
    "product-contract",
    "experience",
    "control-plane",
    "governance",
    "evidence",
    "integration",
    "implementation",
    "other",
)

CONCLUSION_ORDER = {"success": 0, "neutral": 1, "failure": 2, "incomplete": 3}


def load_product_manifest(path: str | Path) -> dict[str, Any]:
    manifest = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("product manifest must be a YAML mapping")
    if manifest.get("schemaVersion") != "iaap-product/v1":
        raise ValueError("product manifest schemaVersion must be iaap-product/v1")

    product = manifest.get("product")
    repositories = manifest.get("repositories")
    if not isinstance(product, dict) or not product.get("id") or not product.get("name"):
        raise ValueError("product manifest requires product.id and product.name")
    if not isinstance(repositories, list) or not repositories:
        raise ValueError("product manifest requires at least one repository")
    if len(repositories) > MAX_PRODUCT_REPOSITORIES:
        raise ValueError(f"product manifest supports at most {MAX_PRODUCT_REPOSITORIES} repositories in V1")

    names: set[str] = set()
    primary_count = 0
    for item in repositories:
        if not isinstance(item, dict):
            raise ValueError("each repository entry must be a mapping")
        name = item.get("name")
        roles = item.get("roles")
        if not isinstance(name, str) or "/" not in name:
            raise ValueError("repository names must use owner/name form")
        if name in names:
            raise ValueError(f"duplicate repository in product manifest: {name}")
        names.add(name)
        if not isinstance(roles, list) or not roles:
            raise ValueError(f"{name}: roles must be a non-empty list")
        unknown = set(roles) - set(ROLE_ORDER)
        if unknown:
            raise ValueError(f"{name}: unknown repository roles: {sorted(unknown)}")
        if item.get("primary") is True:
            primary_count += 1
    if primary_count > 1:
        raise ValueError("product manifest may define at most one primary repository")
    return manifest


def load_scan_results(paths: list[str | Path]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for path in paths:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(raw, dict) or raw.get("schemaVersion") != "scan-result/v1":
            raise ValueError(f"{path}: expected scan-result/v1 JSON")
        results.append(raw)
    return results


def _manifest_digest(manifest: dict[str, Any], results: list[dict[str, Any]]) -> str:
    payload = {
        "manifest": manifest,
        "members": sorted(
            (
                result.get("repository", {}).get("name"),
                result.get("revision", {}).get("sha"),
            )
            for result in results
        ),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_compatibility(results: list[dict[str, Any]]) -> tuple[str | None, str | None]:
    if not results:
        return None, None
    rule_versions = {result.get("ruleCatalogVersion") for result in results}
    scoring_versions = {result.get("scoringModelVersion") for result in results}
    if len(rule_versions) != 1:
        raise ValueError("member scan results use different rule catalog versions")
    if len(scoring_versions) != 1:
        raise ValueError("member scan results use different scoring model versions")
    return next(iter(rule_versions)), next(iter(scoring_versions))


def _aggregate_dimensions(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    order: list[str] = []
    totals: dict[str, dict[str, int]] = {}
    for result in results:
        for item in result.get("dimensionScores", []):
            dimension = item.get("dimension")
            if not isinstance(dimension, str):
                continue
            if dimension not in order:
                order.append(dimension)
            bucket = totals.setdefault(dimension, {"passed": 0, "applicable": 0})
            bucket["passed"] += int(item.get("passed") or 0)
            bucket["applicable"] += int(item.get("applicable") or 0)

    output: list[dict[str, Any]] = []
    for dimension in order:
        bucket = totals[dimension]
        applicable = bucket["applicable"]
        score = round((bucket["passed"] / applicable) * 100) if applicable else None
        output.append(
            {
                "dimension": dimension,
                "passed": bucket["passed"],
                "applicable": applicable,
                "score": score,
            }
        )
    return output


def _overall_score(dimension_scores: list[dict[str, Any]]) -> int | None:
    scores = [item["score"] for item in dimension_scores if item.get("score") is not None]
    return round(sum(scores) / len(scores)) if scores else None


def _member_record(entry: dict[str, Any], result: dict[str, Any] | None) -> dict[str, Any]:
    record: dict[str, Any] = {
        "name": entry["name"],
        "roles": list(entry["roles"]),
        "required": bool(entry.get("required", True)),
        "primary": bool(entry.get("primary", False)),
        "present": result is not None,
    }
    if result is None:
        record.update({"revision": None, "overallScore": None, "conclusion": "incomplete", "findingCount": 0})
    else:
        record.update(
            {
                "revision": result.get("revision"),
                "overallScore": result.get("overallScore"),
                "conclusion": result.get("conclusion"),
                "findingCount": len(result.get("findings") or []),
            }
        )
    return record


def build_product_assessment(
    manifest: dict[str, Any],
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Aggregate repository scan evidence into one logical product assessment.

    Product conclusion is fail-safe: missing required evidence produces INCOMPLETE,
    and any member FAIL keeps the product in failure regardless of the aggregate
    numeric score. Numeric scoring summarizes demonstrated coverage; it never
    overrides a member conclusion.
    """

    manifest_names = [item["name"] for item in manifest["repositories"]]
    by_repo: dict[str, dict[str, Any]] = {}
    for result in results:
        name = (result.get("repository") or {}).get("name")
        if not isinstance(name, str):
            raise ValueError("scan result is missing repository.name")
        if name not in manifest_names:
            raise ValueError(f"scan result is not registered in product manifest: {name}")
        if name in by_repo:
            raise ValueError(f"duplicate scan result for repository: {name}")
        by_repo[name] = result

    rule_version, scoring_version = _validate_compatibility(results)
    members = [_member_record(entry, by_repo.get(entry["name"])) for entry in manifest["repositories"]]
    missing_required = [member["name"] for member in members if member["required"] and not member["present"]]

    present_results = [by_repo[name] for name in manifest_names if name in by_repo]
    dimension_scores = _aggregate_dimensions(present_results)
    overall = _overall_score(dimension_scores)

    member_scores = [member["overallScore"] for member in members if member["overallScore"] is not None]
    minimum_member_score = min(member_scores) if member_scores else None

    findings: list[dict[str, Any]] = []
    for result in present_results:
        repository = result["repository"]["name"]
        for finding in result.get("findings") or []:
            enriched = dict(finding)
            enriched["repository"] = repository
            findings.append(enriched)

    for repository in missing_required:
        findings.append(
            {
                "ruleId": "IAP-PR001",
                "result": "FAIL",
                "dimension": "Evidence Readiness",
                "repository": repository,
                "path": ".iaap/product.yaml",
                "evidence": f"Required product repository {repository} has no supplied scan-result/v1 evidence.",
                "recommendation": "Produce a deterministic IaaP Guard scan for the required product member and include it in the product assessment.",
                "scoring": False,
                "experimental": False,
            }
        )

    if missing_required:
        conclusion = "incomplete"
    else:
        member_conclusions = [member["conclusion"] for member in members if member["present"]]
        conclusion = max(member_conclusions, key=lambda value: CONCLUSION_ORDER.get(str(value), 3), default="success")

    product = manifest["product"]
    return {
        "schemaVersion": "product-assessment/v1",
        "product": {
            "id": product["id"],
            "name": product["name"],
            "owner": product.get("owner"),
        },
        "evidenceRevision": _manifest_digest(manifest, present_results),
        "ruleCatalogVersion": rule_version,
        "scoringModelVersion": scoring_version,
        "acquisition": {
            "mode": "provided-evidence",
            "relatedRepositoryContentRead": False,
            "reciprocalMembershipRequired": False,
        },
        "relationshipEvaluation": {
            "status": "not-evaluated",
            "rules": [],
            "reason": "member scan-result/v1 evidence alone does not reconstruct cross-repository artifact relationships",
        },
        "members": members,
        "completeness": {
            "registered": len(members),
            "present": sum(1 for member in members if member["present"]),
            "missingRequired": missing_required,
            "complete": not missing_required,
        },
        "dimensionScores": dimension_scores,
        "overallScore": overall,
        "minimumMemberScore": minimum_member_score,
        "conclusion": conclusion,
        "findings": findings,
        "boundary": {
            "advisoryProductScope": True,
            "doesNotExpandGitHubAppPermissions": True,
            "memberFailureCannotBeAveragedAway": True,
        },
    }


def render_product_markdown(assessment: dict[str, Any]) -> str:
    product = assessment["product"]
    complete = assessment["completeness"]
    acquisition = assessment["acquisition"]
    relationships = assessment["relationshipEvaluation"]
    lines = [
        f"# IaaP Guard Product Assessment — {product['name']}",
        "",
        f"Product ID: `{product['id']}`  ",
        f"Conclusion: **{str(assessment['conclusion']).upper()}**  ",
        f"Product evidence score: **{assessment['overallScore'] if assessment['overallScore'] is not None else 'N/A'}**  ",
        f"Weakest member score: **{assessment['minimumMemberScore'] if assessment['minimumMemberScore'] is not None else 'N/A'}**  ",
        f"Evidence completeness: **{complete['present']}/{complete['registered']} repositories**  ",
        f"Acquisition: **{acquisition['mode']}**  ",
        f"Relationship evaluation: **{relationships['status']}**  ",
        f"Evidence revision: `{assessment['evidenceRevision']}`",
        "",
        "> Product score summarizes demonstrated coverage. A member FAIL still fails the product, and missing required member evidence produces INCOMPLETE.",
        "",
        "## Member repositories",
        "",
        "| Repository | Roles | Required | Score | Conclusion | Findings |",
        "|---|---|---:|---:|---|---:|",
    ]
    for member in assessment["members"]:
        score = member["overallScore"] if member["overallScore"] is not None else "N/A"
        lines.append(
            f"| `{member['name']}` | {', '.join(member['roles'])} | {'yes' if member['required'] else 'no'} | {score} | {str(member['conclusion']).upper()} | {member['findingCount']} |"
        )

    lines.extend(["", "## Product dimensions", ""])
    for item in assessment["dimensionScores"]:
        score = "N/A" if item["score"] is None else str(item["score"])
        lines.append(f"- **{item['dimension']}** — {score} ({item['passed']}/{item['applicable']})")

    lines.extend(["", "## Findings", ""])
    if not assessment["findings"]:
        lines.append("No current product findings.")
    else:
        for finding in assessment["findings"]:
            location = f"{finding.get('repository', 'unknown')}:{finding.get('path', 'unknown')}"
            if finding.get("line") is not None:
                location += f":{finding['line']}"
            lines.append(
                f"- **{finding.get('result')} {finding.get('ruleId')}** — `{location}` — {finding.get('evidence')}"
            )
    return "\n".join(lines).rstrip() + "\n"
