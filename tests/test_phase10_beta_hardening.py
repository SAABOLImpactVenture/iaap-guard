from __future__ import annotations

import urllib.parse
import unittest

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from iaap_guard.github_app import AppSecrets, CHECK_NAME, GitHubAppError
from iaap_guard.github_beta_runtime import BetaGitHubApi, handle_beta_github_event
from iaap_guard.lambda_handler import _secret_from_aws


class _PagedApi(BetaGitHubApi):
    def __init__(self, pages: dict[int, list[dict]]):
        super().__init__()
        self.pages = pages

    def _request(self, method, path, **kwargs):  # noqa: ARG002
        query = urllib.parse.parse_qs(urllib.parse.urlparse(path).query)
        page = int(query.get("page", ["1"])[0])
        return self.pages.get(page, [])


class _StaleRerequestApi(BetaGitHubApi):
    def installation_token(self, app_jwt, installation_id, repository_id):  # noqa: ARG002
        return "ghs_beta_test"

    def pull_request_head_sha(self, token, repository, pull_number):  # noqa: ARG002
        return "b" * 40


class Phase10BetaHardeningTests(unittest.TestCase):
    def test_renamed_away_supported_file_remains_relevant(self):
        api = _PagedApi(
            {
                1: [
                    {
                        "filename": "architecture/product.txt",
                        "previous_filename": "architecture/product.yaml",
                        "status": "renamed",
                    }
                ]
            }
        )
        paths = api.pull_request_files("token", "example/platform", 7)
        self.assertEqual(paths, ["architecture/product.txt", "architecture/product.yaml"])

    def test_exactly_1000_changed_files_are_accepted(self):
        pages = {
            page: [{"filename": f"docs/file-{page}-{index}.md"} for index in range(100)]
            for page in range(1, 11)
        }
        pages[11] = []
        api = _PagedApi(pages)
        paths = api.pull_request_files("token", "example/platform", 8)
        self.assertEqual(len(paths), 1000)

    def test_more_than_1000_changed_files_are_rejected(self):
        pages = {
            page: [{"filename": f"docs/file-{page}-{index}.md"} for index in range(100)]
            for page in range(1, 11)
        }
        pages[11] = [{"filename": "docs/file-1001.md"}]
        api = _PagedApi(pages)
        with self.assertRaisesRegex(GitHubAppError, "exceeds beta pagination limit"):
            api.pull_request_files("token", "example/platform", 9)

    def test_stale_check_rerequest_is_rejected_before_rescan(self):
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        pem = private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ).decode("utf-8")
        old_sha = "a" * 40
        payload = {
            "action": "rerequested",
            "installation": {"id": 3},
            "repository": {"id": 4, "full_name": "example/platform"},
            "check_run": {
                "name": CHECK_NAME,
                "external_id": f"iaap-guard:9:{old_sha}",
                "head_sha": old_sha,
            },
        }
        result = handle_beta_github_event(
            "check_run",
            payload,
            api=_StaleRerequestApi(),
            secrets=AppSecrets(4529329, pem, "secret"),
        )
        self.assertFalse(result["handled"])
        self.assertEqual(result["revision"], old_sha)
        self.assertEqual(result["currentRevision"], "b" * 40)
        self.assertIn("stale", result["reason"])

    def test_secrets_manager_reader_is_not_process_lifetime_cached(self):
        self.assertFalse(hasattr(_secret_from_aws, "cache_info"))


if __name__ == "__main__":
    unittest.main()
