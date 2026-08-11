from __future__ import annotations

import base64
import io
import tarfile
import unittest
from pathlib import Path

import yaml

from iaap_guard.github_app import _safe_extract_tarball
from iaap_guard.github_product_scope import evaluate_trusted_product_scope


def _tarball(entries: dict[str, bytes]) -> bytes:
    data = io.BytesIO()
    with tarfile.open(fileobj=data, mode="w:gz") as tar:
        for name, body in entries.items():
            info = tarfile.TarInfo(name=name)
            info.size = len(body)
            tar.addfile(info, io.BytesIO(body))
    return data.getvalue()


def _trigger_result():
    return {
        "schemaVersion": "scan-result/v1",
        "ruleCatalogVersion": "iaap-guard/v0.1.2",
        "scoringModelVersion": "coverage/v1",
        "repository": {"name": "example/contracts"},
        "revision": {"sha": "a" * 40, "ref": "refs/pull/7/head"},
        "detectedComponents": ["consumer-contract"],
        "findings": [],
        "ruleResults": [],
        "dimensionScores": [
            {"dimension": "Product Abstraction", "passed": 1, "applicable": 1, "score": 100},
            {"dimension": "Consumer Boundary", "passed": 1, "applicable": 1, "score": 100},
            {"dimension": "Experience / Authority", "passed": 0, "applicable": 0, "score": None},
            {"dimension": "Control-Plane Separation", "passed": 0, "applicable": 0, "score": None},
            {"dimension": "Governance", "passed": 0, "applicable": 0, "score": None},
            {"dimension": "Evidence Readiness", "passed": 0, "applicable": 0, "score": None},
        ],
        "overallScore": 100,
        "conclusion": "success",
    }


def _manifest(related="example/control-plane"):
    return {
        "schemaVersion": "iaap-product/v1",
        "product": {"id": "cloud-foundation", "name": "Cloud Foundation", "owner": "platform-team"},
        "repositories": [
            {"name": "example/contracts", "roles": ["product-contract"], "required": True, "primary": True},
            {"name": related, "roles": ["control-plane", "evidence"], "required": True},
        ],
    }


class _ProductApi:
    def __init__(self, manifest, *, related_visibility="private"):
        self.manifest = manifest
        self.related_visibility = related_visibility
        self.calls = []
        self.token_bodies = []
        self.tarball_calls = []

    def _request(self, method, path, *, token=None, body=None, **kwargs):  # noqa: ARG002
        self.calls.append((method, path, token))
        if path == "/repos/example/contracts":
            return {"default_branch": "main", "visibility": "private", "private": True}
        if path.startswith("/repos/example/contracts/contents/.iaap/product.yaml?ref="):
            content = yaml.safe_dump(self.manifest, sort_keys=False).encode("utf-8")
            return {"type": "file", "encoding": "base64", "content": base64.b64encode(content).decode("ascii")}
        if path == "/repos/example/control-plane/installation":
            return {"id": 77}
        if path == "/app/installations/77/access_tokens":
            self.token_bodies.append(body)
            return {"token": "related-token"}
        if path == "/repos/example/control-plane":
            return {"default_branch": "main", "visibility": self.related_visibility, "private": self.related_visibility != "public"}
        if path == "/repos/example/control-plane/commits/main":
            return {"sha": "b" * 40}
        raise RuntimeError(f"unexpected request: {method} {path}")

    def repository_tarball(self, token, repository, revision):
        self.tarball_calls.append((token, repository, revision))
        return _tarball(
            {
                "repo-related/README.md": b"# Related control plane\n",
                "repo-related/tests/test_evidence.py": b"# deterministic validation evidence\n",
            }
        )


class ProductGitHubScopeTests(unittest.TestCase):
    def test_trusted_default_branch_manifest_drives_related_repo_scope(self):
        api = _ProductApi(_manifest())
        scope = evaluate_trusted_product_scope(
            api=api,
            app_jwt="app-jwt",
            trigger_token="trigger-token",
            trigger_repository="example/contracts",
            trigger_result=_trigger_result(),
            extract_archive=_safe_extract_tarball,
        )
        self.assertIsNotNone(scope)
        assessment, plan = scope
        self.assertTrue(assessment["completeness"]["complete"])
        self.assertEqual(assessment["completeness"]["present"], 2)
        self.assertEqual(plan["schemaVersion"], "product-planning-report/v1")
        manifest_calls = [call for call in api.calls if "/contents/.iaap/product.yaml" in call[1]]
        self.assertEqual(len(manifest_calls), 1)
        self.assertIn("?ref=main", manifest_calls[0][1])

    def test_related_token_is_one_repo_and_contents_read_only(self):
        api = _ProductApi(_manifest())
        evaluate_trusted_product_scope(
            api=api,
            app_jwt="app-jwt",
            trigger_token="trigger-token",
            trigger_repository="example/contracts",
            trigger_result=_trigger_result(),
            extract_archive=_safe_extract_tarball,
        )
        self.assertEqual(
            api.token_bodies,
            [{"repositories": ["control-plane"], "permissions": {"contents": "read"}}],
        )
        self.assertEqual(api.tarball_calls, [("related-token", "example/control-plane", "b" * 40)])

    def test_cross_owner_repository_is_not_read_and_product_is_incomplete(self):
        api = _ProductApi(_manifest(related="other/control-plane"))
        assessment, _ = evaluate_trusted_product_scope(
            api=api,
            app_jwt="app-jwt",
            trigger_token="trigger-token",
            trigger_repository="example/contracts",
            trigger_result=_trigger_result(),
            extract_archive=_safe_extract_tarball,
        )
        self.assertEqual(assessment["conclusion"], "incomplete")
        self.assertEqual(assessment["completeness"]["missingRequired"], ["other/control-plane"])
        self.assertFalse(any("other/control-plane/installation" in call[1] for call in api.calls))

    def test_visibility_mismatch_does_not_become_a_data_bridge(self):
        api = _ProductApi(_manifest(), related_visibility="public")
        assessment, _ = evaluate_trusted_product_scope(
            api=api,
            app_jwt="app-jwt",
            trigger_token="trigger-token",
            trigger_repository="example/contracts",
            trigger_result=_trigger_result(),
            extract_archive=_safe_extract_tarball,
        )
        self.assertEqual(assessment["conclusion"], "incomplete")
        self.assertEqual(api.tarball_calls, [])


if __name__ == "__main__":
    unittest.main()
