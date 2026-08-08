from __future__ import annotations

import io
import json
import os
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from iaap_guard.github_app import (
    AppSecrets,
    CHECK_NAME,
    GitHubApi,
    GitHubAppError,
    PullRequestTarget,
    _safe_extract_tarball,
    create_app_jwt,
    handle_github_event,
    is_relevant_path,
    render_check_output,
    target_from_rerequest,
    verify_webhook_signature,
)
from iaap_guard.lambda_handler import lambda_handler


class _BytesResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False


class _RecordingOpener:
    def __init__(self, response: bytes):
        self.response = response
        self.requests = []

    def open(self, request, timeout=30):  # noqa: ARG002
        self.requests.append(request)
        return _BytesResponse(self.response)


def _tarball(entries: dict[str, bytes], *, symlink: tuple[str, str] | None = None) -> bytes:
    data = io.BytesIO()
    with tarfile.open(fileobj=data, mode="w:gz") as tar:
        for name, body in entries.items():
            info = tarfile.TarInfo(name=name)
            info.size = len(body)
            tar.addfile(info, io.BytesIO(body))
        if symlink:
            info = tarfile.TarInfo(name=symlink[0])
            info.type = tarfile.SYMTYPE
            info.linkname = symlink[1]
            tar.addfile(info)
    return data.getvalue()


class _FakeEvaluationApi:
    def __init__(self, files: list[str], archive: bytes | None = None):
        self.files = files
        self.archive = archive
        self.token_request = None
        self.upsert = None

    def installation_token(self, app_jwt, installation_id, repository_id):
        self.token_request = (app_jwt, installation_id, repository_id)
        return "ghs_stateless_format_is_not_assumed_to_be_40_chars"

    def pull_request_files(self, token, repository, pull_number):  # noqa: ARG002
        return list(self.files)

    def repository_tarball(self, token, repository, revision):  # noqa: ARG002
        if self.archive is None:
            raise AssertionError("archive should not have been requested")
        return self.archive

    def upsert_check_run(self, token, target, result, *, no_relevant_changes):  # noqa: ARG002
        self.upsert = (target, result, no_relevant_changes)
        return {"id": 9001}


class Phase10GitHubAppTests(unittest.TestCase):
    def test_webhook_signature_matches_github_published_vector(self):
        secret = "It's a Secret to Everybody"
        payload = b"Hello, World!"
        signature = "sha256=757107ea0eb2509fc211221cce984b8a37570b6d7586c22c46f4379c8b043e17"
        self.assertTrue(verify_webhook_signature(payload, secret, signature))
        self.assertFalse(verify_webhook_signature(payload + b"!", secret, signature))
        self.assertFalse(verify_webhook_signature(payload, secret, None))

    def test_app_jwt_is_rs256_with_bounded_claims(self):
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        pem = private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ).decode("utf-8")
        token = create_app_jwt(4529329, pem, now=1_000_000)
        claims = jwt.decode(
            token,
            private_key.public_key(),
            algorithms=["RS256"],
            options={"verify_exp": False, "verify_iat": False},
        )
        self.assertEqual(claims["iss"], 4529329)
        self.assertIsInstance(claims["iss"], int)
        self.assertEqual(claims["iat"], 999_940)
        self.assertEqual(claims["exp"], 1_000_540)
        self.assertLessEqual(claims["exp"] - 1_000_000, 600)

    def test_installation_token_is_scoped_to_triggering_repo_and_minimum_permissions(self):
        opener = _RecordingOpener(json.dumps({"token": "ghs_APPID_JWT_variable_length"}).encode("utf-8"))
        api = GitHubApi(opener=opener)
        token = api.installation_token("app-jwt", 77, 12345)
        self.assertEqual(token, "ghs_APPID_JWT_variable_length")
        request = opener.requests[0]
        body = json.loads(request.data.decode("utf-8"))
        self.assertEqual(body["repository_ids"], [12345])
        self.assertEqual(
            body["permissions"],
            {"contents": "read", "pull_requests": "read", "checks": "write"},
        )
        self.assertEqual(request.headers["Authorization"], "Bearer app-jwt")

    def test_relevant_path_filter_matches_scanner_surface(self):
        self.assertTrue(is_relevant_path("platform/product.yaml"))
        self.assertTrue(is_relevant_path("README.md"))
        self.assertTrue(is_relevant_path("infra/main.tf"))
        self.assertFalse(is_relevant_path("docs/diagram.png"))
        self.assertFalse(is_relevant_path("archive.zip"))

    def test_safe_archive_extracts_regular_files_and_rejects_escape_or_links(self):
        good = _tarball({"repo-abc/README.md": b"# hello\n", "repo-abc/config/policy.yaml": b"kind: Test\n"})
        with tempfile.TemporaryDirectory() as tmp:
            root = _safe_extract_tarball(good, Path(tmp))
            self.assertEqual((root / "README.md").read_text(encoding="utf-8"), "# hello\n")

        bad_path = _tarball({"../escape.txt": b"bad"})
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(GitHubAppError):
                _safe_extract_tarball(bad_path, Path(tmp))

        bad_link = _tarball({}, symlink=("repo-abc/link", "/etc/passwd"))
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(GitHubAppError):
                _safe_extract_tarball(bad_link, Path(tmp))

    def test_no_relevant_change_publishes_success_without_downloading_repository(self):
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        pem = private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ).decode("utf-8")
        api = _FakeEvaluationApi(["docs/architecture.png"])
        payload = {
            "action": "opened",
            "number": 4,
            "installation": {"id": 88},
            "repository": {"id": 991, "full_name": "example/platform"},
            "pull_request": {"head": {"sha": "a" * 40}},
        }
        result = handle_github_event(
            "pull_request",
            payload,
            api=api,
            secrets=AppSecrets(4529329, pem, "secret"),
        )
        self.assertTrue(result["handled"])
        self.assertEqual(result["conclusion"], "success")
        self.assertIsNone(result["score"])
        self.assertEqual(result["relevantFiles"], 0)
        self.assertTrue(api.upsert[2])

    def test_relevant_change_scans_snapshot_with_real_core(self):
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        pem = private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ).decode("utf-8")
        archive = _tarball(
            {
                "repo-abc/product.yaml": (
                    b"apiVersion: platform.example.org/v1alpha1\n"
                    b"kind: InfrastructureProductSchema\n"
                    b"spec:\n"
                    b"  required: [owner]\n"
                    b"  properties:\n"
                    b"    owner:\n"
                    b"      type: string\n"
                ),
                "repo-abc/tests/test_contract.py": b"# deterministic validation evidence\n",
            }
        )
        api = _FakeEvaluationApi(["product.yaml"], archive)
        payload = {
            "action": "synchronize",
            "number": 5,
            "installation": {"id": 89},
            "repository": {"id": 992, "full_name": "example/product"},
            "pull_request": {"head": {"sha": "b" * 40}},
        }
        result = handle_github_event(
            "pull_request",
            payload,
            api=api,
            secrets=AppSecrets(4529329, pem, "secret"),
        )
        self.assertTrue(result["handled"])
        self.assertEqual(result["repository"], "example/product")
        self.assertEqual(result["revision"], "b" * 40)
        self.assertEqual(result["relevantFiles"], 1)
        self.assertFalse(api.upsert[2])
        self.assertEqual(api.upsert[1]["repository"]["name"], "example/product")

    def test_check_output_preserves_core_conclusion_semantics(self):
        base = {
            "repository": {"name": "example/platform"},
            "revision": {"sha": "c" * 40},
            "ruleCatalogVersion": "iaap-guard/v0.1.2",
            "scoringModelVersion": "coverage/v1",
            "overallScore": 100,
            "findings": [],
        }
        for conclusion, label in (("success", "PASS"), ("neutral", "WARNING"), ("failure", "FAIL")):
            result = dict(base, conclusion=conclusion)
            output = render_check_output(result)
            self.assertIn(label, output["title"])
            self.assertIn("iaap-guard/v0.1.2", output["text"])

    def test_existing_check_is_updated_instead_of_duplicated(self):
        class RecordingApi(GitHubApi):
            def __init__(self):
                super().__init__()
                self.call = None

            def check_runs_for_revision(self, token, repository, revision):  # noqa: ARG002
                return [{"id": 42, "name": CHECK_NAME, "external_id": "iaap-guard:7:" + "d" * 40}]

            def _request(self, method, path, **kwargs):
                self.call = (method, path, kwargs.get("body"))
                return {"id": 42}

        api = RecordingApi()
        target = PullRequestTarget("example/platform", 1, 7, "d" * 40, 2, "refs/pull/7/head")
        result = {
            "repository": {"name": target.repository},
            "revision": {"sha": target.head_sha},
            "ruleCatalogVersion": "iaap-guard/v0.1.2",
            "scoringModelVersion": "coverage/v1",
            "overallScore": 100,
            "findings": [],
            "conclusion": "success",
        }
        api.upsert_check_run("token", target, result, no_relevant_changes=False)
        self.assertEqual(api.call[0], "PATCH")
        self.assertTrue(api.call[1].endswith("/check-runs/42"))
        self.assertNotIn("head_sha", api.call[2])

    def test_rerequest_reuses_external_identity_only_for_guard_check(self):
        payload = {
            "action": "rerequested",
            "installation": {"id": 3},
            "repository": {"id": 4, "full_name": "example/platform"},
            "check_run": {
                "name": CHECK_NAME,
                "external_id": "iaap-guard:9:" + "e" * 40,
                "head_sha": "e" * 40,
            },
        }
        target = target_from_rerequest(payload)
        self.assertIsNotNone(target)
        self.assertEqual(target.pull_number, 9)
        payload["check_run"]["name"] = "Other Check"
        self.assertIsNone(target_from_rerequest(payload))

    def test_lambda_rejects_bad_signature_before_event_processing(self):
        event = {
            "requestContext": {"http": {"method": "POST"}},
            "headers": {"x-hub-signature-256": "sha256=bad", "x-github-event": "ping"},
            "body": "{}",
            "isBase64Encoded": False,
        }
        with patch.dict(
            os.environ,
            {
                "IAAP_GUARD_GITHUB_PRIVATE_KEY": "not-used-for-invalid-signature",
                "IAAP_GUARD_GITHUB_WEBHOOK_SECRET": "secret",
            },
            clear=False,
        ):
            response = lambda_handler(event, None)
        self.assertEqual(response["statusCode"], 401)
        self.assertEqual(json.loads(response["body"])["error"], "invalid_webhook_signature")


if __name__ == "__main__":
    unittest.main()
