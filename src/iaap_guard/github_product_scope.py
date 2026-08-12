from __future__ import annotations

import base64
import tempfile
import urllib.parse
from pathlib import Path
from typing import Any, Callable

from .loader import load_artifacts
from .product import MAX_PRODUCT_REPOSITORIES, build_product_assessment, load_product_manifest
from .product_planning import build_product_planning_report
from .product_relationships import RELATIONSHIP_RULE_IDS, apply_relationship_evidence
from .readiness import build_readiness_report, requirement
from .scanner import scan_path

PRODUCT_MANIFEST_PATH = ".iaap/product.yaml"
MAX_RELATIONSHIP_BUNDLE_BYTES = 20_000_000
RELATIONSHIP_CONTEXTS = {"consumer-contract", "experience"}


def _encoded_repo(repository: str) -> str:
    return urllib.parse.quote(repository, safe="/")


def _repository_metadata(api: Any, token: str, repository: str) -> dict[str, Any]:
    response = api._request("GET", f"/repos/{_encoded_repo(repository)}", token=token)
    if not isinstance(response, dict):
        raise RuntimeError("repository metadata response was not an object")
    return response


def _trusted_manifest(
    api: Any,
    token: str,
    repository: str,
    *,
    metadata: dict[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Load product membership from a repository default branch, never PR head."""

    metadata = metadata if metadata is not None else _repository_metadata(api, token, repository)
    default_branch = metadata.get("default_branch")
    if not isinstance(default_branch, str) or not default_branch:
        raise RuntimeError("repository metadata did not contain a default branch")
    encoded_ref = urllib.parse.quote(default_branch, safe="")
    try:
        response = api._request(
            "GET",
            f"/repos/{_encoded_repo(repository)}/contents/{PRODUCT_MANIFEST_PATH}?ref={encoded_ref}",
            token=token,
        )
    except RuntimeError as exc:
        if "HTTP 404" in str(exc):
            return None, metadata
        raise
    if not isinstance(response, dict) or response.get("type") != "file":
        return None, metadata
    content = response.get("content")
    encoding = response.get("encoding")
    if encoding != "base64" or not isinstance(content, str):
        raise RuntimeError("trusted product manifest response was not base64 file content")
    try:
        text = base64.b64decode(content, validate=False).decode("utf-8")
    except (ValueError, UnicodeDecodeError) as exc:
        raise RuntimeError("trusted product manifest could not be decoded") from exc

    with tempfile.TemporaryDirectory(prefix="iaap-guard-product-manifest-") as tmp:
        path = Path(tmp) / "product.yaml"
        path.write_text(text, encoding="utf-8")
        manifest = load_product_manifest(path)
    return manifest, metadata


def _membership_signature(manifest: dict[str, Any]) -> tuple[Any, ...]:
    product = manifest["product"]
    repositories = tuple(
        sorted(
            (
                item["name"],
                tuple(sorted(item["roles"])),
                bool(item.get("required", True)),
                bool(item.get("primary", False)),
            )
            for item in manifest["repositories"]
        )
    )
    return (
        product["id"],
        product["name"],
        product.get("owner"),
        repositories,
    )


def _related_repository_token(api: Any, app_jwt: str, repository: str) -> str:
    installation = api._request(
        "GET",
        f"/repos/{_encoded_repo(repository)}/installation",
        token=app_jwt,
    )
    installation_id = installation.get("id") if isinstance(installation, dict) else None
    if not isinstance(installation_id, int):
        raise RuntimeError("related repository is not accessible through an IaaP Guard installation")
    short_name = repository.split("/", 1)[1]
    response = api._request(
        "POST",
        f"/app/installations/{installation_id}/access_tokens",
        token=app_jwt,
        body={
            "repositories": [short_name],
            "permissions": {"contents": "read"},
        },
    )
    token = response.get("token") if isinstance(response, dict) else None
    if not isinstance(token, str) or not token:
        raise RuntimeError("related repository token response did not contain a token")
    return token


def _visibility(metadata: dict[str, Any]) -> str:
    value = metadata.get("visibility")
    if isinstance(value, str):
        return value
    return "private" if metadata.get("private") else "public"


def _default_revision(
    api: Any,
    token: str,
    repository: str,
    metadata: dict[str, Any],
) -> tuple[str, str]:
    default_branch = metadata.get("default_branch")
    if not isinstance(default_branch, str) or not default_branch:
        raise RuntimeError("related repository metadata did not contain a default branch")
    encoded_branch = urllib.parse.quote(default_branch, safe="")
    commit = api._request(
        "GET",
        f"/repos/{_encoded_repo(repository)}/commits/{encoded_branch}",
        token=token,
    )
    sha = commit.get("sha") if isinstance(commit, dict) else None
    if not isinstance(sha, str) or len(sha) != 40:
        raise RuntimeError("related repository default branch did not resolve to a commit SHA")
    return default_branch, sha


def _member_destination(bundle: Path, repository: str) -> Path:
    owner, name = repository.split("/", 1)
    return bundle / "members" / owner / name


def _copy_relationship_artifacts(
    bundle: Path,
    repository: str,
    root: Path,
    used_bytes: int,
) -> tuple[int, bool]:
    """Copy only artifacts that can participate in the V1 relationship rule.

    Member repository scans still operate on the full extracted snapshot. The
    shared bundle is a separate bounded derivative containing only classified
    consumer-contract/experience artifacts needed by IAP-C001.
    """

    destination = _member_destination(bundle, repository)
    for artifact in load_artifacts(root):
        if not RELATIONSHIP_CONTEXTS.intersection(artifact.contexts):
            continue
        raw = artifact.text.encode("utf-8")
        if used_bytes + len(raw) > MAX_RELATIONSHIP_BUNDLE_BYTES:
            return used_bytes, False
        target = destination / artifact.relative_path
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        except OSError:
            return used_bytes, False
        used_bytes += len(raw)
    return used_bytes, True


def _mark_relationship_incomplete(assessment: dict[str, Any], reason: str) -> None:
    assessment["relationshipEvaluation"] = {
        "status": "incomplete",
        "rules": sorted(RELATIONSHIP_RULE_IDS),
        "reason": reason,
    }
    assessment["findings"].append(
        {
            "ruleId": "IAP-PR002",
            "result": "FAIL",
            "dimension": "Evidence Readiness",
            "repository": "@product",
            "path": ".iaap/product.yaml",
            "evidence": reason,
            "recommendation": "Reduce or split the registered product relationship evidence so the bounded product compatibility evaluation can complete.",
            "scoring": False,
            "experimental": False,
        }
    )
    assessment["conclusion"] = "incomplete"


def evaluate_trusted_product_scope(
    *,
    api: Any,
    app_jwt: str,
    trigger_token: str,
    trigger_repository: str,
    trigger_root: Path,
    trigger_result: dict[str, Any],
    extract_archive: Callable[[bytes, Path], Path],
    include_readiness: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]] | tuple[dict[str, Any] | None, dict[str, Any] | None, dict[str, Any]] | None:
    """Evaluate one logical product using explicitly and reciprocally registered evidence."""

    diagnostics: list[dict[str, Any]] = []
    member_readiness: list[dict[str, Any]] = []
    try:
        manifest, trigger_metadata = _trusted_manifest(api, trigger_token, trigger_repository)
    except (RuntimeError, ValueError) as exc:
        if not include_readiness:
            raise
        diagnostics.append(requirement("IAP-RDY101", "Trusted product registration", "BLOCKED", str(exc), "Guard cannot establish the intended trusted product boundary.", "Correct the default-branch .iaap/product.yaml or repository metadata, then rerun Guard.", repository=trigger_repository, path=PRODUCT_MANIFEST_PATH))
        return None, None, build_readiness_report("product", trigger_repository, None, diagnostics)
    if manifest is None:
        return None
    repositories = manifest["repositories"]
    if len(repositories) > MAX_PRODUCT_REPOSITORIES:
        raise RuntimeError(f"product manifest exceeds V1 limit of {MAX_PRODUCT_REPOSITORIES} repositories")

    registered = {item["name"] for item in repositories}
    if trigger_repository not in registered:
        if not include_readiness:
            raise RuntimeError("trusted product manifest does not register the triggering repository")
        diagnostics.append(requirement("IAP-RDY101", "Trusted product registration", "BLOCKED", f"{trigger_repository} is absent from its trusted manifest.", "A repository cannot safely activate a product boundary that omits itself.", f"Add {trigger_repository} to the reciprocal default-branch membership declaration.", repository=trigger_repository, path=PRODUCT_MANIFEST_PATH))
        return None, None, build_readiness_report("product", trigger_repository, manifest["product"], diagnostics)

    diagnostics.append(requirement("IAP-RDY101", "Trusted product registration", "READY", "The triggering default branch contains valid, self-registering iaap-product/v1 membership.", "Guard can evaluate the declared trust boundary.", "No action required.", repository=trigger_repository, path=PRODUCT_MANIFEST_PATH))

    expected_membership = _membership_signature(manifest)
    trigger_owner = trigger_repository.split("/", 1)[0]
    trigger_visibility = _visibility(trigger_metadata)

    results = [trigger_result]
    related_content_read = False
    relationship_bundle_complete = True
    relationship_bundle_bytes = 0

    with tempfile.TemporaryDirectory(prefix="iaap-guard-product-bundle-") as bundle_tmp:
        bundle = Path(bundle_tmp)
        relationship_bundle_bytes, relationship_bundle_complete = _copy_relationship_artifacts(
            bundle,
            trigger_repository,
            trigger_root,
            relationship_bundle_bytes,
        )

        for entry in repositories:
            repository = entry["name"]
            required = bool(entry.get("required", True))
            if repository == trigger_repository:
                member_readiness.append({"repository": repository, "required": required, "status": "READY", "observed": "Trigger repository evidence is available."})
                continue
            if repository.split("/", 1)[0] != trigger_owner:
                status = "BLOCKED" if required else "ADVISORY"
                diagnostics.append(requirement("IAP-RDY102", "Same-owner federation boundary", status, f"{repository} is not owned by {trigger_owner}.", "V1 automatic federation does not cross GitHub owners.", "Use a same-owner product boundary or keep this relationship outside automatic V1 federation.", severity="blocking" if required else "advisory", repository=repository))
                member_readiness.append({"repository": repository, "required": required, "status": "BLOCKED" if required else "READY_WITH_ADVISORIES", "observed": "Owner boundary mismatch."})
                continue
            try:
                token = _related_repository_token(api, app_jwt, repository)
                metadata = _repository_metadata(api, token, repository)
                if _visibility(metadata) != trigger_visibility:
                    # Do not read even the trusted product manifest across the
                    # V1 visibility boundary. This prevents product federation
                    # from becoming a configuration-probing side channel.
                    status = "BLOCKED" if required else "ADVISORY"
                    diagnostics.append(requirement("IAP-RDY103", "Member visibility boundary", status, f"{repository} visibility {_visibility(metadata)} does not match trigger visibility {trigger_visibility}.", "Guard intentionally does not read product content across the V1 visibility boundary.", "Align visibility or keep the relationship outside automatic federation.", severity="blocking" if required else "advisory", repository=repository))
                    member_readiness.append({"repository": repository, "required": required, "status": "BLOCKED" if required else "READY_WITH_ADVISORIES", "observed": "Visibility mismatch."})
                    continue
                related_manifest, _ = _trusted_manifest(
                    api,
                    token,
                    repository,
                    metadata=metadata,
                )
                related_content_read = True
                if related_manifest is None:
                    status = "BLOCKED" if required else "ADVISORY"
                    diagnostics.append(requirement("IAP-RDY105", "Trusted default-branch manifest", status, f"{repository} default branch does not contain {PRODUCT_MANIFEST_PATH}.", "Trusted federation cannot include this member.", "Merge the identical iaap-product/v1 declaration into the member default branch.", severity="blocking" if required else "advisory", repository=repository, path=PRODUCT_MANIFEST_PATH))
                    member_readiness.append({"repository": repository, "required": required, "status": "BLOCKED" if required else "READY_WITH_ADVISORIES", "observed": "Trusted manifest is missing."})
                    continue
                if _membership_signature(related_manifest) != expected_membership:
                    status = "BLOCKED" if required else "ADVISORY"
                    diagnostics.append(requirement("IAP-RDY106", "Reciprocal product membership", status, f"{repository} default-branch identity or membership signature does not match the trigger declaration.", "Trusted federation cannot include the member; required-member assessment becomes INCOMPLETE.", "Merge the identical iaap-product/v1 declaration into the member default branch.", severity="blocking" if required else "advisory", repository=repository, path=PRODUCT_MANIFEST_PATH))
                    member_readiness.append({"repository": repository, "required": required, "status": "BLOCKED" if required else "READY_WITH_ADVISORIES", "observed": "Reciprocal membership mismatch."})
                    continue
                default_branch, sha = _default_revision(api, token, repository, metadata)
                archive = api.repository_tarball(token, repository, sha)
                with tempfile.TemporaryDirectory(prefix="iaap-guard-related-") as tmp:
                    root = extract_archive(archive, Path(tmp))
                    result = scan_path(
                        root,
                        repository=repository,
                        revision=sha,
                        ref=f"refs/heads/{default_branch}",
                    )
                    if relationship_bundle_complete:
                        relationship_bundle_bytes, relationship_bundle_complete = _copy_relationship_artifacts(
                            bundle,
                            repository,
                            root,
                            relationship_bundle_bytes,
                        )
                results.append(result)
                diagnostics.append(requirement("IAP-RDY108", "Member evidence acquisition", "READY", f"{repository} resolved to immutable default-branch SHA {sha} and bounded evidence was acquired.", "The member can participate in product evaluation.", "No action required.", repository=repository))
                member_readiness.append({"repository": repository, "required": required, "status": "READY", "observed": f"Evidence acquired at {sha}."})
            except (RuntimeError, ValueError) as exc:
                # A malformed or inaccessible related member is unavailable
                # product evidence; required members make the assessment
                # INCOMPLETE instead of failing the triggering webhook.
                status = "BLOCKED" if required else "ADVISORY"
                observed = str(exc)
                if "commit SHA" in observed:
                    requirement_id, name = "IAP-RDY107", "Immutable default-branch revision"
                    remediation = f"Ensure {repository}'s default branch resolves to an immutable Git commit SHA."
                elif "manifest" in observed:
                    requirement_id, name = "IAP-RDY105", "Trusted default-branch manifest"
                    remediation = "Correct the member default-branch manifest to the existing iaap-product/v1 contract."
                elif "archive" in observed or "snapshot" in observed:
                    requirement_id, name = "IAP-RDY108", "Member evidence acquisition"
                    remediation = "Bring the repository snapshot within existing Guard archive/file bounds and rerun Guard."
                else:
                    requirement_id, name = "IAP-RDY104", "Member App access and metadata"
                    remediation = f"Grant the existing IaaP Guard App installation access to {repository} and ensure it has a default branch. No new permission type is required."
                diagnostics.append(requirement(requirement_id, name, status, f"{repository}: {observed}", "Guard cannot acquire trusted evidence; a required-member assessment becomes INCOMPLETE.", remediation, severity="blocking" if required else "advisory", repository=repository))
                member_readiness.append({"repository": repository, "required": required, "status": "BLOCKED" if required else "READY_WITH_ADVISORIES", "observed": str(exc)})
                continue

        assessment = build_product_assessment(manifest, results)
        assessment["acquisition"] = {
            "mode": "trusted-github-federation",
            "relatedRepositoryContentRead": related_content_read,
            "reciprocalMembershipRequired": True,
        }

        if not assessment["completeness"]["complete"]:
            _mark_relationship_incomplete(
                assessment,
                "Cross-repository compatibility could not be fully evaluated because required product member evidence is missing.",
            )
        elif not relationship_bundle_complete:
            _mark_relationship_incomplete(
                assessment,
                f"Cross-repository compatibility evidence exceeded the V1 bounded bundle limit of {MAX_RELATIONSHIP_BUNDLE_BYTES} bytes or could not be copied safely.",
            )
        else:
            relationship_scan = scan_path(
                bundle,
                repository=f"product:{manifest['product']['id']}",
                revision=assessment["evidenceRevision"][:40],
                ref="iaap-product/v1",
            )
            assessment = apply_relationship_evidence(assessment, relationship_scan)
            assessment["relationshipEvaluation"] = {
                "status": "complete",
                "rules": sorted(RELATIONSHIP_RULE_IDS),
                "reason": None,
            }

    plan = build_product_planning_report(assessment)
    if include_readiness:
        required_count = sum(bool(item.get("required", True)) for item in repositories)
        ready_required = sum(item["required"] and item["status"] == "READY" for item in member_readiness)
        status = "READY" if ready_required == required_count else "BLOCKED"
        diagnostics.append(requirement("IAP-RDY109", "Required-member completeness", status, f"{ready_required}/{required_count} required repositories are ready.", "Missing required readiness prevents a safe complete product evaluation.", "Resolve the member-specific blockers before relying on Product Assessment." if status == "BLOCKED" else "No action required.", repository=trigger_repository))
        relationship_status = "READY" if relationship_bundle_complete and assessment["relationshipEvaluation"]["status"] != "incomplete" else "BLOCKED"
        diagnostics.append(requirement("IAP-RDY110", "Bounded product relationship evaluation", relationship_status, f"Relationship evaluation is {assessment['relationshipEvaluation']['status']} within the {MAX_RELATIONSHIP_BUNDLE_BYTES}-byte V1 bundle bound.", "An incomplete relationship evaluation cannot support a complete product-health claim.", "Reduce or split relationship evidence or resolve missing required members before Product Assessment." if relationship_status == "BLOCKED" else "No action required.", repository=trigger_repository))
        readiness = build_readiness_report("product", trigger_repository, manifest["product"], diagnostics, member_readiness)
        readiness["boundary"]["localNetworkAccess"] = True
        return assessment, plan, readiness
    return assessment, plan
