from __future__ import annotations

import base64
import hashlib
import hmac
import io
import json
import os
import tarfile
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Callable

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from .loader import SUPPORTED_SUFFIXES
from .scanner import scan_path

GITHUB_API_VERSION = "2026-03-10"
CHECK_NAME = "IaaP Guard / Architecture"
ALLOWED_PULL_REQUEST_ACTIONS = {"opened", "synchronize", "reopened", "ready_for_review"}
MAX_ARCHIVE_BYTES = 25_000_000
MAX_ARCHIVE_MEMBERS = 20_000
MAX_EXTRACTED_BYTES = 100_000_000
MAX_CHECK_TEXT = 60_000


class GitHubAppError(RuntimeError):
    pass


class RepositorySnapshotTooLarge(GitHubAppError):
    pass


@dataclass(frozen=True)
class PullRequestTarget:
    repository: str
    repository_id: int
    pull_number: int
    head_sha: str
    installation_id: int
    ref: str

    @property
    def external_id(self) -> str:
        return f"iaap-guard:{self.pull_number}:{self.head_sha}"


@dataclass(frozen=True)
class AppSecrets:
    app_id: int
    private_key: str
    webhook_secret: str


def verify_webhook_signature(payload: bytes, secret: str, signature: str | None) -> bool:
    if not signature or not signature.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def _base64url_json(value: dict[str, Any]) -> bytes:
    raw = json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return base64.urlsafe_b64encode(raw).rstrip(b"=")


def create_app_jwt(app_id: int, private_key: str, now: int | None = None) -> str:
    if isinstance(app_id, bool) or not isinstance(app_id, int) or app_id <= 0:
        raise ValueError("GitHub App ID must be a positive integer")
    issued = int(time.time() if now is None else now)
    header = _base64url_json({"alg": "RS256", "typ": "JWT"})
    payload = _base64url_json({"iat": issued - 60, "exp": issued + 540, "iss": app_id})
    signing_input = header + b"." + payload
    try:
        key = serialization.load_pem_private_key(private_key.encode("utf-8"), password=None)
    except (TypeError, ValueError) as exc:
        raise GitHubAppError("GitHub App private key is not a valid PEM private key") from exc
    if not isinstance(key, rsa.RSAPrivateKey):
        raise GitHubAppError("GitHub App private key must be RSA for RS256")
    signature = key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
    encoded_signature = base64.urlsafe_b64encode(signature).rstrip(b"=")
    return b".".join((header, payload, encoded_signature)).decode("ascii")


def is_relevant_path(filename: str) -> bool:
    return Path(filename).suffix.lower() in SUPPORTED_SUFFIXES


def no_relevant_result(repository: str, revision: str, ref: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="iaap-guard-empty-") as tmp:
        return scan_path(tmp, repository=repository, revision=revision, ref=ref)


class _SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Follow GitHub archive redirects without forwarding bearer auth cross-host."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is None:
            return None
        old_host = urllib.parse.urlparse(req.full_url).netloc.lower()
        new_host = urllib.parse.urlparse(newurl).netloc.lower()
        if old_host != new_host:
            redirected.remove_header("Authorization")
        return redirected


class GitHubApi:
    def __init__(self, base_url: str = "https://api.github.com", opener: Any | None = None):
        self.base_url = base_url.rstrip("/")
        self.opener = opener or urllib.request.build_opener(_SafeRedirectHandler())

    def _request(
        self,
        method: str,
        path: str,
        *,
        token: str | None = None,
        body: dict[str, Any] | None = None,
        accept_json: bool = True,
        max_bytes: int | None = None,
    ) -> Any:
        url = path if path.startswith("https://") else f"{self.base_url}{path}"
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "iaap-guard-phase-10-beta",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        data = None
        if body is not None:
            data = json.dumps(body, separators=(",", ":")).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with self.opener.open(request, timeout=30) as response:
                if max_bytes is None:
                    raw = response.read()
                else:
                    raw = response.read(max_bytes + 1)
                    if len(raw) > max_bytes:
                        raise RepositorySnapshotTooLarge(
                            f"repository archive exceeds beta limit of {max_bytes} bytes"
                        )
                if not accept_json:
                    return raw
                return json.loads(raw.decode("utf-8")) if raw else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read(4096).decode("utf-8", errors="replace")
            raise GitHubAppError(f"GitHub API {method} {path} failed: HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise GitHubAppError(f"GitHub API {method} {path} failed: {exc.reason}") from exc

    def installation_token(self, app_jwt: str, installation_id: int, repository_id: int) -> str:
        response = self._request(
            "POST",
            f"/app/installations/{installation_id}/access_tokens",
            token=app_jwt,
            body={
                "repository_ids": [repository_id],
                "permissions": {
                    "contents": "read",
                    "pull_requests": "read",
                    "checks": "write",
                },
            },
        )
        token = response.get("token")
        if not isinstance(token, str) or not token:
            raise GitHubAppError("installation-token response did not contain a token")
        return token

    def pull_request_files(self, token: str, repository: str, pull_number: int) -> list[str]:
        filenames: list[str] = []
        for page in range(1, 11):
            encoded = urllib.parse.quote(repository, safe="/")
            response = self._request(
                "GET",
                f"/repos/{encoded}/pulls/{pull_number}/files?per_page=100&page={page}",
                token=token,
            )
            if not isinstance(response, list):
                raise GitHubAppError("pull-request files response was not a list")
            for item in response:
                filename = item.get("filename") if isinstance(item, dict) else None
                if isinstance(filename, str):
                    filenames.append(filename)
            if len(response) < 100:
                break
        else:
            raise GitHubAppError("pull request exceeds beta pagination limit of 1000 changed files")
        return filenames

    def repository_tarball(self, token: str, repository: str, revision: str) -> bytes:
        encoded = urllib.parse.quote(repository, safe="/")
        rev = urllib.parse.quote(revision, safe="")
        return self._request(
            "GET",
            f"/repos/{encoded}/tarball/{rev}",
            token=token,
            accept_json=False,
            max_bytes=MAX_ARCHIVE_BYTES,
        )

    def check_runs_for_revision(self, token: str, repository: str, revision: str) -> list[dict[str, Any]]:
        encoded_repo = urllib.parse.quote(repository, safe="/")
        encoded_name = urllib.parse.quote(CHECK_NAME, safe="")
        response = self._request(
            "GET",
            f"/repos/{encoded_repo}/commits/{revision}/check-runs?check_name={encoded_name}&per_page=100",
            token=token,
        )
        runs = response.get("check_runs") if isinstance(response, dict) else None
        return runs if isinstance(runs, list) else []

    def upsert_check_run(
        self,
        token: str,
        target: PullRequestTarget,
        result: dict[str, Any],
        *,
        no_relevant_changes: bool,
    ) -> dict[str, Any]:
        output = render_check_output(result, no_relevant_changes=no_relevant_changes)
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


def _iso8601_now(now: float | None = None) -> str:
    value = time.time() if now is None else now
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(value))


def _safe_extract_tarball(archive: bytes, destination: Path) -> Path:
    total = 0
    top_levels: set[str] = set()
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
        members = tar.getmembers()
        if len(members) > MAX_ARCHIVE_MEMBERS:
            raise RepositorySnapshotTooLarge(
                f"repository archive exceeds beta limit of {MAX_ARCHIVE_MEMBERS} members"
            )
        for member in members:
            member_path = PurePosixPath(member.name)
            if member_path.is_absolute() or ".." in member_path.parts:
                raise GitHubAppError("repository archive contains an unsafe path")
            if member.issym() or member.islnk() or member.isdev() or member.isfifo():
                raise GitHubAppError("repository archive contains an unsupported link or device entry")
            if member_path.parts:
                top_levels.add(member_path.parts[0])
            if member.isfile():
                total += member.size
                if total > MAX_EXTRACTED_BYTES:
                    raise RepositorySnapshotTooLarge(
                        f"repository archive exceeds beta extracted-size limit of {MAX_EXTRACTED_BYTES} bytes"
                    )
                target = destination.joinpath(*member_path.parts).resolve()
                if not target.is_relative_to(destination.resolve()):
                    raise GitHubAppError("repository archive path escapes extraction root")
                target.parent.mkdir(parents=True, exist_ok=True)
                source = tar.extractfile(member)
                if source is None:
                    raise GitHubAppError("repository archive member could not be read")
                with target.open("wb") as handle:
                    handle.write(source.read())
            elif member.isdir():
                target = destination.joinpath(*member_path.parts).resolve()
                if not target.is_relative_to(destination.resolve()):
                    raise GitHubAppError("repository archive directory escapes extraction root")
                target.mkdir(parents=True, exist_ok=True)
    if len(top_levels) == 1:
        candidate = destination / next(iter(top_levels))
        if candidate.is_dir():
            return candidate
    return destination


def _finding_lines(result: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for finding in result.get("findings", [])[:50]:
        location = finding.get("path", "unknown")
        if finding.get("line"):
            location += f":{finding['line']}"
        experimental = " · experimental" if finding.get("experimental") else ""
        lines.append(
            f"- **{finding.get('result')} {finding.get('ruleId')}**{experimental} — "
            f"`{location}` — {finding.get('evidence')}\n  - Recommendation: {finding.get('recommendation')}"
        )
    if len(result.get("findings", [])) > 50:
        lines.append(f"- … {len(result['findings']) - 50} additional findings omitted from Check text.")
    return lines


def render_check_output(result: dict[str, Any], *, no_relevant_changes: bool = False) -> dict[str, str]:
    conclusion = result["conclusion"]
    label = {"success": "PASS", "neutral": "WARNING", "failure": "FAIL"}[conclusion]
    score = "N/A" if result.get("overallScore") is None else str(result["overallScore"])
    summary = (
        "No IaaP-relevant files changed; deterministic repository scan was not required."
        if no_relevant_changes
        else f"Architecture conclusion: **{label}** · score **{score}** · findings **{len(result.get('findings', []))}**."
    )
    text_lines = [
        f"Repository: `{result['repository']['name']}`",
        f"Revision: `{result['revision']['sha']}`",
        f"Ruleset: `{result['ruleCatalogVersion']}`",
        f"Scoring: `{result['scoringModelVersion']}`",
        "",
    ]
    if no_relevant_changes:
        text_lines.append("No changed file matched the deterministic V0 analysis suffix set.")
    elif result.get("findings"):
        text_lines.extend(["### Findings", "", *_finding_lines(result)])
    else:
        text_lines.append("No WARNING or FAIL findings.")
    text = "\n".join(text_lines)
    if len(text) > MAX_CHECK_TEXT:
        text = text[: MAX_CHECK_TEXT - 16] + "\n… truncated."
    return {"title": f"{CHECK_NAME} — {label}", "summary": summary, "text": text}


def target_from_pull_request(payload: dict[str, Any]) -> PullRequestTarget:
    repository = payload.get("repository") or {}
    installation = payload.get("installation") or {}
    pull = payload.get("pull_request") or {}
    head = pull.get("head") or {}
    full_name = repository.get("full_name")
    repository_id = repository.get("id")
    installation_id = installation.get("id")
    pull_number = payload.get("number")
    head_sha = head.get("sha")
    if not (
        isinstance(full_name, str)
        and isinstance(repository_id, int)
        and isinstance(installation_id, int)
        and isinstance(pull_number, int)
        and isinstance(head_sha, str)
    ):
        raise GitHubAppError("pull_request payload is missing repository, installation, PR number, or head SHA")
    return PullRequestTarget(
        repository=full_name,
        repository_id=repository_id,
        pull_number=pull_number,
        head_sha=head_sha,
        installation_id=installation_id,
        ref=f"refs/pull/{pull_number}/head",
    )


def target_from_rerequest(payload: dict[str, Any]) -> PullRequestTarget | None:
    check = payload.get("check_run") or {}
    if check.get("name") != CHECK_NAME:
        return None
    external_id = check.get("external_id")
    if not isinstance(external_id, str) or not external_id.startswith("iaap-guard:"):
        return None
    parts = external_id.split(":", 2)
    if len(parts) != 3:
        return None
    try:
        pull_number = int(parts[1])
    except ValueError:
        return None
    repository = payload.get("repository") or {}
    installation = payload.get("installation") or {}
    full_name = repository.get("full_name")
    repository_id = repository.get("id")
    installation_id = installation.get("id")
    head_sha = check.get("head_sha")
    if not (
        isinstance(full_name, str)
        and isinstance(repository_id, int)
        and isinstance(installation_id, int)
        and isinstance(head_sha, str)
    ):
        raise GitHubAppError("check_run payload is missing repository, installation, or head SHA")
    if parts[2] != head_sha:
        return None
    return PullRequestTarget(
        repository=full_name,
        repository_id=repository_id,
        pull_number=pull_number,
        head_sha=head_sha,
        installation_id=installation_id,
        ref=f"refs/pull/{pull_number}/head",
    )


def evaluate_target(api: GitHubApi, secrets: AppSecrets, target: PullRequestTarget) -> dict[str, Any]:
    app_jwt = create_app_jwt(secrets.app_id, secrets.private_key)
    token = api.installation_token(app_jwt, target.installation_id, target.repository_id)
    changed_files = api.pull_request_files(token, target.repository, target.pull_number)
    relevant = [name for name in changed_files if is_relevant_path(name)]
    if not relevant:
        result = no_relevant_result(target.repository, target.head_sha, target.ref)
        check = api.upsert_check_run(token, target, result, no_relevant_changes=True)
        return {"result": result, "check": check, "relevantFiles": 0, "changedFiles": len(changed_files)}

    archive = api.repository_tarball(token, target.repository, target.head_sha)
    with tempfile.TemporaryDirectory(prefix="iaap-guard-repo-") as tmp:
        root = _safe_extract_tarball(archive, Path(tmp))
        result = scan_path(
            root,
            repository=target.repository,
            revision=target.head_sha,
            ref=target.ref,
        )
    check = api.upsert_check_run(token, target, result, no_relevant_changes=False)
    return {
        "result": result,
        "check": check,
        "relevantFiles": len(relevant),
        "changedFiles": len(changed_files),
    }


def handle_github_event(
    event_name: str,
    payload: dict[str, Any],
    *,
    api: GitHubApi,
    secrets: AppSecrets,
) -> dict[str, Any]:
    action = payload.get("action")
    target: PullRequestTarget | None = None
    if event_name == "pull_request":
        if action not in ALLOWED_PULL_REQUEST_ACTIONS:
            return {"handled": False, "reason": f"pull_request action {action!r} is outside V0"}
        target = target_from_pull_request(payload)
    elif event_name == "check_run" and action == "rerequested":
        target = target_from_rerequest(payload)
        if target is None:
            return {"handled": False, "reason": "rerequest is not an IaaP Guard check"}
    else:
        return {"handled": False, "reason": f"event {event_name!r} action {action!r} is outside V0"}

    evaluated = evaluate_target(api, secrets, target)
    result = evaluated["result"]
    check = evaluated["check"] if isinstance(evaluated.get("check"), dict) else {}
    return {
        "handled": True,
        "repository": target.repository,
        "pullNumber": target.pull_number,
        "revision": target.head_sha,
        "conclusion": result["conclusion"],
        "score": result["overallScore"],
        "findings": len(result["findings"]),
        "changedFiles": evaluated["changedFiles"],
        "relevantFiles": evaluated["relevantFiles"],
        "checkRunId": check.get("id"),
    }
