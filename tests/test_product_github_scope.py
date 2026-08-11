from __future__ import annotations

import base64
import io
import tarfile
import tempfile
import unittest
from contextlib import contextmanager
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


@contextmanager
def _trigger_root(files: dict[str, str] | None = None):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source = files or {"README.md": "# Trigger repository\n"}
        for relative, text in source.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        yield root


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


def _manifest(related="example/control-plane", roles=None):
    return {
        "schemaVersion": "iaap-product/v1",
        "product": {"id": "cloud-foundation", "name": "Cloud Foundation", "owner": "platform-team"},
        "repositories": [
            {"name": "example/contracts", "roles": ["product-contract"], "required": True, "primary": True},
            {"name": related, "roles": roles or ["control-plane", "evidence"], "required": True},
        ],
    }


class _ProductApi:
    def __init__(
        self,
        manifest,
        *,
        related_visibility="private",
        related_entries=None,
        related_manifest=None,
    ):
        self.manifest = manifest
        self.related_manifest = manifest if related_manifest is None else related_manifest
        self.related_visibility = related_visibility
        self.related_repository = manifest["repositories"][1]["name"]
        self.related_entries = related_entries or {
            "repo-related/README.md": b"# Related control plane\n",
            "repo-related/tests/test_evidence.py": b"# deterministic validation evidence\n",
        }
        self.calls = []
        self.token_bodies = []
        self.tarball_calls = []

    @staticmethod
    def _manifest_response(manifest):
        content = yaml.safe_dump(manifest, sort_keys=False).encode("utf-8")
        return {"type": "file", "encoding": "base64", "content": base64.b64encode(content).decode("ascii")}

    def _request(self, method, path, *, token=None, body=None, **kwargs):  # noqa: ARG002
        self.calls.append((method, path, token))
        if path == "/repos/example/contracts":
            return {"default_branch": "main", "visibility": "private", "private": True}
        if path.startswith("/repos/example/contracts/contents/.iaap/product.yaml?ref="):
            return self._manifest_response(self.manifest)
        if path == f"/repos/{self.related_repository}/installation":
            return {"id": 77}
        if path == "/app/installations/77/access_tokens":
            self.token_bodies.append(body)
            return {"token": "related-token"}
        if path == f"/repos/{self.related_repository}":
            return {"default_branch": "main", "visibility": self.related_visibility, "private": self.related_visibility != "public"}
        if path.startswith(f"/repos/{self.related_repository}/contents/.iaap/product.yaml?ref="):
            return self._manifest_response(self.related_manifest)
        if path == f"/repos/{self.related_repository}/commits/main":
            return {"sha": "b" * 40}
        raise RuntimeError(f"unexpected request: {method} {path}")

    def repository_tarball(self, token, repository, revision):
        self.tarball_calls.append((token, repository, revision))
        return _tarball(self.related_entries)


def _evaluate(api):
    with _trigger_root() as root:
        return evaluate_trusted_product_scope(
            api=api,
            app_jwt="app-jwt",
            trigger_token="trigger-token",
            trigger_repository="example/contracts",
            trigger_root=root,
            trigger_result=_trigger_result(),
            extract_archive=_safe_extract_tarball,
        )


class ProductGitHubScopeTests(unittest.TestCase):
    def test_trusted_default_branch_manifests_drive_related_repo_scope(self):
        api = _ProductApi(_manifest())
        scope = _evaluate(api)
        self.assertIsNotNone(scope)
        assessment, plan = scope
        self.assertTrue(assessment["completeness"]["complete"])
        self.assertEqual(assessment["completeness"]["present"], 2)
        self.assertEqual(plan["schemaVersion"], "product-planning-report/v1")
        manifest_calls = [call for call in api.calls if "/contents/.iaap/product.yaml" in call[1]]
        self.assertEqual(len(manifest_calls), 2)
        self.assertTrue(all("?ref=main" in call[1] for call in manifest_calls))

    def test_related_token_is_one_repo_and_contents_read_only(self):
        api = _ProductApi(_manifest())
        _evaluate(api)
        self.assertEqual(
            api.token_bodies,
            [{"repositories": ["control-plane"], "permissions": {"contents": "read"}}],
        )
        self.assertEqual(api.tarball_calls, [("related-token", "example/control-plane", "b" * 40)])

    def test_nonreciprocal_product_membership_is_not_read_as_product_evidence(self):
        manifest = _manifest()
        other = _manifest()
        other["product"] = {"id": "different-product", "name": "Different Product", "owner": "platform-team"}
        api = _ProductApi(manifest, related_manifest=other)
        assessment, _ = _evaluate(api)
        self.assertEqual(assessment["conclusion"], "incomplete")
        self.assertEqual(assessment["completeness"]["missingRequired"], ["example/control-plane"])
        self.assertEqual(api.tarball_calls, [])

    def test_cross_owner_repository_is_not_read_and_product_is_incomplete(self):
        api = _ProductApi(_manifest(related="other/control-plane"))
        assessment, _ = _evaluate(api)
        self.assertEqual(assessment["conclusion"], "incomplete")
        self.assertEqual(assessment["completeness"]["missingRequired"], ["other/control-plane"])
        self.assertFalse(any("other/control-plane/installation" in call[1] for call in api.calls))

    def test_visibility_mismatch_does_not_become_a_data_bridge(self):
        api = _ProductApi(_manifest(), related_visibility="public")
        assessment, _ = _evaluate(api)
        self.assertEqual(assessment["conclusion"], "incomplete")
        self.assertEqual(api.tarball_calls, [])

    def test_cross_repo_contract_mismatch_becomes_product_relationship_finding(self):
        manifest = _manifest(related="example/storefront", roles=["experience"])
        storefront = b"""apiVersion: scaffolder.backstage.io/v1beta3
kind: Template
metadata:
  name: cloud-foundation
spec:
  parameters:
    - title: Product request
      required: [owner, cloud]
      properties:
        owner:
          type: string
        cloud:
          type: string
          enum: [aws, azure]
"""
        api = _ProductApi(
            manifest,
            related_entries={
                "repo-related/template.yaml": storefront,
                "repo-related/tests/test_contract.py": b"# deterministic contract validation\n",
            },
        )
        canonical = """apiVersion: platform.example.org/v1alpha1
kind: InfrastructureProductSchema
metadata:
  name: cloud-foundation
spec:
  required: [owner, cloud]
  properties:
    owner:
      type: string
    cloud:
      type: string
      enum: [aws, gcp]
"""
        with _trigger_root({"product.yaml": canonical, "tests/test_contract.py": "# deterministic contract validation\n"}) as root:
            assessment, plan = evaluate_trusted_product_scope(
                api=api,
                app_jwt="app-jwt",
                trigger_token="trigger-token",
                trigger_repository="example/contracts",
                trigger_root=root,
                trigger_result=_trigger_result(),
                extract_archive=_safe_extract_tarball,
            )
        compatibility = [item for item in assessment["findings"] if item["ruleId"] == "IAP-C001"]
        self.assertEqual(len(compatibility), 1)
        self.assertEqual(compatibility[0]["repository"], "example/storefront")
        self.assertIn("azure", compatibility[0]["evidence"])
        self.assertTrue(any(epic["ruleId"] == "IAP-C001" for objective in plan["objectives"] for epic in objective["epics"]))


if __name__ == "__main__":
    unittest.main()
