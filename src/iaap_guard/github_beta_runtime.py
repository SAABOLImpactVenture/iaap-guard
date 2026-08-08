from __future__ import annotations

import urllib.parse
from typing import Any

from .github_app import (
    AppSecrets,
    GitHubApi,
    GitHubAppError,
    create_app_jwt,
    handle_github_event,
    target_from_rerequest,
)


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
