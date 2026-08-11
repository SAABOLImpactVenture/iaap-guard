from __future__ import annotations

import urllib.parse
from typing import Any

from .github_app import (
    AppSecrets,
    CHECK_NAME,
    GitHubApi,
    GitHubAppError,
    MAX_CHECK_TEXT,
    PullRequestTarget,
    _iso8601_now,
    create_app_jwt,
    handle_github_event,
    render_check_output,
    target_from_rerequest,
)
from .planning import build_planning_report, render_planning_markdown


def render_beta_check_output(
    result: dict[str, Any],
    *,
    no_relevant_changes: bool = False,
) -> dict[str, str]:
    """Render the existing architecture Check plus the advisory planning layer.

    The deterministic scan remains authoritative. The planning section is an
    adapter over planning-report/v1 and appears only when Guard has findings to
    remediate.
    """

    output = render_check_output(result, no_relevant_changes=no_relevant_changes)
    if no_relevant_changes or not result.get("findings"):
        return output

    report = build_planning_report(result)
    planning_text = render_planning_markdown(report, include_header=False).rstrip()
    totals = report["totals"]
    output["summary"] += (
        f" Improvement plan: {totals['objectives']} objectives · "
        f"{totals['keyResults']} key results · {totals['epics']} epics."
    )
    combined = output["text"] + "\n\n### Improvement Plan\n\n" + planning_text
    if len(combined) > MAX_CHECK_TEXT:
        combined = combined[: MAX_CHECK_TEXT - 16] + "\n… truncated."
    output["text"] = combined
    return output


class BetaGitHubApi(GitHubApi):
    """GitHub API adapter with live-beta boundary hardening.

    The deterministic scanner and rule engine remain unchanged. These guards
    address GitHub transport/event semantics discovered during the public beta.
    """

    def pull_request_files(self, token: str, repository: str, pull_number: int) -> list[str]:
        """Return paths relevant to change detection, including renamed-away paths.

        GitHub exposes the new path as ``filename`` and the old path as
        ``previous_filename`` for renamed files. Both are considered for
        relevance so removing/renaming an analyzer-supported file cannot be
        misclassified as "no relevant changes".

        Up to 1000 changed files are accepted. Page 11 is queried only to
        distinguish exactly 1000 files from more than 1000.
        """

        paths: list[str] = []
        encoded = urllib.parse.quote(repository, safe="/")
        for page in range(1, 12):
            response = self._request(
                "GET",
                f"/repos/{encoded}/pulls/{pull_number}/files?per_page=100&page={page}",
                token=token,
            )
            if not isinstance(response, list):
                raise GitHubAppError("pull-request files response was not a list")

            if page == 11:
                if response:
                    raise GitHubAppError("pull request exceeds beta pagination limit of 1000 changed files")
                break

            for item in response:
                if not isinstance(item, dict):
                    continue
                filename = item.get("filename")
                previous = item.get("previous_filename")
                if isinstance(filename, str):
                    paths.append(filename)
                if isinstance(previous, str) and previous != filename:
                    paths.append(previous)

            if len(response) < 100:
                break

        return paths

    def pull_request_head_sha(self, token: str, repository: str, pull_number: int) -> str:
        encoded = urllib.parse.quote(repository, safe="/")
        response = self._request(
            "GET",
            f"/repos/{encoded}/pulls/{pull_number}",
            token=token,
        )
        pull = response if isinstance(response, dict) else {}
        head = pull.get("head") if isinstance(pull.get("head"), dict) else {}
        sha = head.get("sha")
        if not isinstance(sha, str) or not sha:
            raise GitHubAppError("pull-request response did not contain a current head SHA")
        return sha

    def upsert_check_run(
        self,
        token: str,
        target: PullRequestTarget,
        result: dict[str, Any],
        *,
        no_relevant_changes: bool,
    ) -> dict[str, Any]:
        output = render_beta_check_output(result, no_relevant_changes=no_relevant_changes)
        base_payload = {
            "name": CHECK_NAME,
            "external_id": target.external_id,
            "status": "completed",
            "conclusion": result["conclusion"],
            "completed_at": _iso8601_now(),
            "output": output,
        }
        existing = next(
            (
                run
                for run in self.check_runs_for_revision(token, target.repository, target.head_sha)
                if run.get("external_id") == target.external_id and run.get("name") == CHECK_NAME
            ),
            None,
        )
        encoded_repo = urllib.parse.quote(target.repository, safe="/")
        if existing and isinstance(existing.get("id"), int):
            return self._request(
                "PATCH",
                f"/repos/{encoded_repo}/check-runs/{existing['id']}",
                token=token,
                body=base_payload,
            )
        payload = dict(base_payload)
        payload["head_sha"] = target.head_sha
        return self._request(
            "POST",
            f"/repos/{encoded_repo}/check-runs",
            token=token,
            body=payload,
        )


def handle_beta_github_event(
    event_name: str,
    payload: dict[str, Any],
    *,
    api: BetaGitHubApi,
    secrets: AppSecrets,
) -> dict[str, Any]:
    """Apply GitHub-event safety checks, then delegate to the proven handler."""

    if event_name == "check_run" and payload.get("action") == "rerequested":
        target = target_from_rerequest(payload)
        if target is not None:
            app_jwt = create_app_jwt(secrets.app_id, secrets.private_key)
            token = api.installation_token(app_jwt, target.installation_id, target.repository_id)
            current_head = api.pull_request_head_sha(token, target.repository, target.pull_number)
            if current_head != target.head_sha:
                return {
                    "handled": False,
                    "reason": "rerequested check is stale relative to the pull request head",
                    "repository": target.repository,
                    "pullNumber": target.pull_number,
                    "revision": target.head_sha,
                    "currentRevision": current_head,
                }

    return handle_github_event(event_name, payload, api=api, secrets=secrets)
