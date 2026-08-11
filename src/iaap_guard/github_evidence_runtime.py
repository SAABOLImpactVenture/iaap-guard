from __future__ import annotations

import tempfile
import time
import urllib.parse
from pathlib import Path
from typing import Any

from .evidence import build_evidence_manifest
from .github_app import (
    AppSecrets,
    CHECK_NAME,
    MAX_CHECK_TEXT,
    PullRequestTarget,
    _safe_extract_tarball,
    create_app_jwt,
    target_from_pull_request,
    target_from_rerequest,
)
from .github_beta_runtime import BetaGitHubApi, handle_beta_github_event, render_beta_check_output
from .scanner import scan_path


def _target(event_name: str, payload: dict[str, Any]) -> PullRequestTarget | None:
    if event_name == "pull_request":
        return target_from_pull_request(payload)
    if event_name == "check_run" and payload.get("action") == "rerequested":
        return target_from_rerequest(payload)
    return None


def _completed_at() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _pull_request_base_sha(
    api: BetaGitHubApi,
    token: str,
    repository: str,
    pull_number: int,
) -> str | None:
    encoded = urllib.parse.quote(repository, safe="/")
    response = api._request(
        "GET",
        f"/repos/{encoded}/pulls/{pull_number}",
        token=token,
    )
    pull = response if isinstance(response, dict) else {}
    base = pull.get("base") if isinstance(pull.get("base"), dict) else {}
    sha = base.get("sha")
    return sha if isinstance(sha, str) and len(sha) == 40 else None


def _base_sha_from_event(
    event_name: str,
    payload: dict[str, Any],
    *,
    api: BetaGitHubApi,
    token: str,
    target: PullRequestTarget,
) -> str | None:
    if event_name == "pull_request":
        pull = payload.get("pull_request") if isinstance(payload.get("pull_request"), dict) else {}
        base = pull.get("base") if isinstance(pull.get("base"), dict) else {}
        sha = base.get("sha")
        if isinstance(sha, str) and len(sha) == 40:
            return sha
    return _pull_request_base_sha(api, token, target.repository, target.pull_number)


def _scan_revision(
    api: BetaGitHubApi,
    token: str,
    target: PullRequestTarget,
    revision: str,
    *,
    ref: str,
    prefix: str,
) -> dict[str, Any]:
    archive = api.repository_tarball(token, target.repository, revision)
    with tempfile.TemporaryDirectory(prefix=prefix) as tmp:
        root = _safe_extract_tarball(archive, Path(tmp))
        return scan_path(
            root,
            repository=target.repository,
            revision=revision,
            ref=ref,
        )


def append_evidence_output(
    output: dict[str, str],
    manifest: dict[str, Any] | None,
) -> dict[str, str]:
    if manifest is None:
        return output

    output = dict(output)
    continuity = manifest["evidenceContinuity"]
    change = manifest["changeAssessment"]
    disposition = manifest["disposition"]
    status = str(continuity["status"])
    display_status = status.replace("_", " ").upper()
    baseline = manifest.get("baselineRevision") or {}
    baseline_sha = baseline.get("sha") if isinstance(baseline, dict) else None
    baseline_label = baseline_sha if isinstance(baseline_sha, str) else "not established"

    output["summary"] += f" Evidence continuity: **{display_status}** against the PR base."

    transitions = change.get("ruleTransitions") or []
    delta = change.get("findingDelta") or {}
    reasons = continuity.get("reasons") or []
    lines = [
        "### Evidence Continuity",
        "",
        f"- PR-base revision: `{baseline_label}`",
        f"- Status: **{display_status}**",
        f"- Guard materiality: `{change['materiality']}`",
        f"- Disposition: `{disposition['status']}`",
        f"- Rule-state transitions: **{len(transitions)}**",
        f"- Finding evidence: **{len(delta.get('introduced') or [])} introduced / {len(delta.get('resolved') or [])} resolved**",
        f"- Evidence digest: `{manifest['evidenceDigest']}`",
    ]
    if reasons:
        lines.append("- Reasons: " + ", ".join(f"`{reason}`" for reason in reasons))
    lines.extend(
        [
            "",
            "Evidence continuity is not authorization continuity. The PR-base comparison is advisory and does not change the repository architecture Check conclusion or determine legal, institutional, deployment, exception, or disposition authority.",
        ]
    )

    combined = output["text"] + "\n\n---\n\n" + "\n".join(lines)
    if len(combined) > MAX_CHECK_TEXT:
        combined = combined[: MAX_CHECK_TEXT - 16] + "\n… truncated."
    output["text"] = combined
    return output


def _replace_check_output(
    api: BetaGitHubApi,
    token: str,
    target: PullRequestTarget,
    result: dict[str, Any],
    output: dict[str, str],
) -> dict[str, Any]:
    existing = next(
        (
            run
            for run in api.check_runs_for_revision(token, target.repository, target.head_sha)
            if run.get("external_id") == target.external_id and run.get("name") == CHECK_NAME
        ),
        None,
    )
    encoded_repo = urllib.parse.quote(target.repository, safe="/")
    payload = {
        "name": CHECK_NAME,
        "external_id": target.external_id,
        "status": "completed",
        # Evidence continuity is advisory in Phase 14. The deterministic
        # repository scan continues to own the Check conclusion.
        "conclusion": result["conclusion"],
        "completed_at": _completed_at(),
        "output": output,
    }
    if existing and isinstance(existing.get("id"), int):
        return api._request(
            "PATCH",
            f"/repos/{encoded_repo}/check-runs/{existing['id']}",
            token=token,
            body=payload,
        )
    payload["head_sha"] = target.head_sha
    return api._request(
        "POST",
        f"/repos/{encoded_repo}/check-runs",
        token=token,
        body=payload,
    )


def handle_evidence_aware_event(
    event_name: str,
    payload: dict[str, Any],
    *,
    api: BetaGitHubApi,
    secrets: AppSecrets,
) -> dict[str, Any]:
    """Run the proven beta event path, then compare PR head to PR-base Guard evidence.

    The base revision is supplied by the GitHub pull-request object (or fetched
    from the pull request for a Check rerequest), not by repository content in
    the untrusted PR head. The resulting evidence-manifest/v1 remains advisory:
    repository scan semantics continue to own the GitHub Check conclusion.
    """

    result = handle_beta_github_event(event_name, payload, api=api, secrets=secrets)
    if not result.get("handled") or int(result.get("relevantFiles") or 0) == 0:
        return result

    target = _target(event_name, payload)
    if target is None:
        return result

    app_jwt = create_app_jwt(secrets.app_id, secrets.private_key)
    token = api.installation_token(app_jwt, target.installation_id, target.repository_id)
    base_sha = _base_sha_from_event(
        event_name,
        payload,
        api=api,
        token=token,
        target=target,
    )

    current = _scan_revision(
        api,
        token,
        target,
        target.head_sha,
        ref=target.ref,
        prefix="iaap-guard-evidence-head-",
    )
    baseline = None
    if base_sha is not None:
        baseline = _scan_revision(
            api,
            token,
            target,
            base_sha,
            ref=f"refs/pull/{target.pull_number}/base",
            prefix="iaap-guard-evidence-base-",
        )

    manifest = build_evidence_manifest(current, baseline)
    output = render_beta_check_output(current, no_relevant_changes=False)
    output = append_evidence_output(output, manifest)
    check = _replace_check_output(api, token, target, current, output)

    result["checkRunId"] = check.get("id", result.get("checkRunId"))
    result["evidenceContinuity"] = {
        "status": manifest["evidenceContinuity"]["status"],
        "materiality": manifest["changeAssessment"]["materiality"],
        "disposition": manifest["disposition"]["status"],
        "baselineRevision": base_sha,
        "evidenceDigest": manifest["evidenceDigest"],
    }
    # Product-aware rendering consumes this internally so a later product-scope
    # Check replacement preserves the evidence section. It is removed before the
    # Lambda response is returned.
    result["_evidenceManifest"] = manifest
    return result
