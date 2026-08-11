from __future__ import annotations

import base64
import shutil
import tempfile
import urllib.parse
from pathlib import Path
from typing import Any, Callable

from .product import MAX_PRODUCT_REPOSITORIES, build_product_assessment, load_product_manifest
from .product_planning import build_product_planning_report
from .product_relationships import apply_relationship_evidence
from .scanner import scan_path

PRODUCT_MANIFEST_PATH = ".iaap/product.yaml"


def _encoded_repo(repository: str) -> str:
    return urllib.parse.quote(repository, safe="/")


def _repository_metadata(api: Any, token: str, repository: str) -> dict[str, Any]:
    response = api._request("GET", f"/repos/{_encoded_repo(repository)}", token=token)
    if not isinstance(response, dict):
        raise RuntimeError("repository metadata response was not an object")
    return response


def _trusted_manifest(api: Any, token: str, repository: str) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Load product membership from a repository default branch, never PR head."""

    metadata = _repository_metadata(api, token, repository)
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


def _copy_member(bundle: Path, repository: str, root: Path) -> None:
    destination = _member_destination(bundle, repository)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(root, destination, dirs_exist_ok=True)


def evaluate_trusted_product_scope(
    *,
    api: Any,
    app_jwt: str,
    trigger_token: str,
    trigger_repository: str,
    trigger_root: Path,
    trigger_result: dict[str, Any],
    extract_archive: Callable[[bytes, Path], Path],
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    """Evaluate one logical product using explicitly and reciprocally registered evidence.

    V1 safety boundaries:
    - membership is read only from trusted default branches, never PR heads;
    - every automatically federated member must carry the same product membership;
    - the triggering repository must be registered;
    - related repositories must share the same owner and visibility;
    - every related token is scoped to exactly one repository and contents:read;
    - inaccessible or non-reciprocal required members become INCOMPLETE;
    - related repositories are scanned at immutable default-branch SHAs;
    - cross-repo relationship rules run only after members are safely assembled.
    """

    manifest, trigger_metadata = _trusted_manifest(api, trigger_token, trigger_repository)
    if manifest is None:
        return None
    repositories = manifest["repositories"]
    if len(repositories) > MAX_PRODUCT_REPOSITORIES:
        raise RuntimeError(f"product manifest exceeds V1 limit of {MAX_PRODUCT_REPOSITORIES} repositories")

    registered = {item["name"] for item in repositories}
    if trigger_repository not in registered:
        raise RuntimeError("trusted product manifest does not register the triggering repository")

    expected_membership = _membership_signature(manifest)
    trigger_owner = trigger_repository.split("/", 1)[0]
    trigger_visibility = trigger_metadata.get("visibility")
    if not isinstance(trigger_visibility, str):
        trigger_visibility = "private" if trigger_metadata.get("private") else "public"

    results = [trigger_result]
    with tempfile.TemporaryDirectory(prefix="iaap-guard-product-bundle-") as bundle_tmp:
        bundle = Path(bundle_tmp)
        _copy_member(bundle, trigger_repository, trigger_root)

        for entry in repositories:
            repository = entry["name"]
            if repository == trigger_repository:
                continue
            if repository.split("/", 1)[0] != trigger_owner:
                continue
            try:
                token = _related_repository_token(api, app_jwt, repository)
                related_manifest, metadata = _trusted_manifest(api, token, repository)
                if related_manifest is None or _membership_signature(related_manifest) != expected_membership:
                    # A triggering repository cannot unilaterally enroll another
                    # repository into product-level evidence sharing. The related
                    # repository must reciprocally declare the same product scope.
                    continue
                visibility = metadata.get("visibility")
                if not isinstance(visibility, str):
                    visibility = "private" if metadata.get("private") else "public"
                if visibility != trigger_visibility:
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
                    _copy_member(bundle, repository, root)
                results.append(result)
            except RuntimeError:
                # Fail closed at the product layer. Required members become
                # INCOMPLETE; optional members remain visible as absent evidence.
                continue

        assessment = build_product_assessment(manifest, results)
        relationship_scan = scan_path(
            bundle,
            repository=f"product:{manifest['product']['id']}",
            revision=assessment["evidenceRevision"][:40],
            ref="iaap-product/v1",
        )
        assessment = apply_relationship_evidence(assessment, relationship_scan)

    plan = build_product_planning_report(assessment)
    return assessment, plan
