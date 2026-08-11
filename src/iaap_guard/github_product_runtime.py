from __future__ import annotations

import tempfile
import time
import urllib.parse
from pathlib import Path
from typing import Any

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
from .github_product_scope import evaluate_trusted_product_scope
from .product import render_product_markdown
from .product_planning import render_product_planning_markdown
from .scanner import scan_path


def _target(event_name: str, payload: dict[str, Any]) -> PullRequestTarget | None:
    if event_name == "pull_request":
        return target_from_pull_request(payload)
    if event_name == "check_run" and payload.get("action") == "rerequested":
        return target_from_rerequest(payload)
    return None


def _completed_at() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _append_product_output(
    output: dict[str, str],
    assessment: dict[str, Any],
    plan: dict[str, Any],
) -> dict[str, str]:
    product = assessment["product"]
    completeness = assessment["completeness"]
    output = dict(output)
    output["summary"] += (
        f" Product `{product['name']}`: **{str(assessment['conclusion']).upper()}** · "
        f"score **{assessment['overallScore'] if assessment['overallScore'] is not None else 'N/A'}** · "
        f"evidence **{completeness['present']}/{completeness['registered']} repos**."
    )
    product_text = render_product_markdown(assessment).rstrip()
    plan_text = render_product_planning_markdown(plan).rstrip()
    combined = output["text"] + "\n\n---\n\n" + product_text + "\n\n" + plan_text
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
        # Product scope is advisory in V1. Repository semantics continue to own
        # the Check conclusion so a related-repo issue cannot unexpectedly turn
        # an unrelated PR into a blocking failure.
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


def handle_product_aware_event(
    event_name: str,
    payload: dict[str, Any],
    *,
    api: BetaGitHubApi,
    secrets: AppSecrets,
) -> dict[str, Any]:
    """Run the proven repository event path, then add trusted product context.

    The repository scan remains authoritative for Check success/neutral/failure.
    Product scope is an advisory second layer built from explicit default-branch
    registration and immutable member repository snapshots.
    """

    base = handle_beta_github_event(event_name, payload, api=api, secrets=secrets)
    if not base.get("handled") or int(base.get("relevantFiles") or 0) == 0:
        return base

    target = _target(event_name, payload)
    if target is None:
        return base

    app_jwt = create_app_jwt(secrets.app_id, secrets.private_key)
    trigger_token = api.installation_token(app_jwt, target.installation_id, target.repository_id)
    archive = api.repository_tarball(trigger_token, target.repository, target.head_sha)
    with tempfile.TemporaryDirectory(prefix="iaap-guard-product-trigger-") as tmp:
        root = _safe_extract_tarball(archive, Path(tmp))
        trigger_result = scan_path(
            root,
            repository=target.repository,
            revision=target.head_sha,
            ref=target.ref,
        )

    product_scope = evaluate_trusted_product_scope(
        api=api,
        app_jwt=app_jwt,
        trigger_token=trigger_token,
        trigger_repository=target.repository,
        trigger_result=trigger_result,
        extract_archive=_safe_extract_tarball,
    )
    if product_scope is None:
        return base

    assessment, plan = product_scope
    output = render_beta_check_output(trigger_result, no_relevant_changes=False)
    output = _append_product_output(output, assessment, plan)
    check = _replace_check_output(api, trigger_token, target, trigger_result, output)

    base["checkRunId"] = check.get("id", base.get("checkRunId"))
    base["product"] = {
        "id": assessment["product"]["id"],
        "name": assessment["product"]["name"],
        "conclusion": assessment["conclusion"],
        "score": assessment["overallScore"],
        "minimumMemberScore": assessment["minimumMemberScore"],
        "registeredRepositories": assessment["completeness"]["registered"],
        "presentRepositories": assessment["completeness"]["present"],
        "evidenceRevision": assessment["evidenceRevision"],
    }
    return base
