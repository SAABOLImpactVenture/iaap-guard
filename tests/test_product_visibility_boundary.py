from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from iaap_guard.github_product_scope import evaluate_trusted_product_scope


MANIFEST = {
    "schemaVersion": "iaap-product/v1",
    "product": {"id": "cloud-foundation", "name": "Cloud Foundation", "owner": "platform-team"},
    "repositories": [
        {"name": "example/contracts", "roles": ["product-contract"], "required": True, "primary": True},
        {"name": "example/private-control", "roles": ["control-plane"], "required": True},
    ],
}

TRIGGER_RESULT = {
    "schemaVersion": "scan-result/v1",
    "ruleCatalogVersion": "iaap-guard/v0.1.2",
    "scoringModelVersion": "coverage/v1",
    "repository": {"name": "example/contracts"},
    "revision": {"sha": "a" * 40},
    "detectedComponents": [],
    "findings": [],
    "ruleResults": [],
    "dimensionScores": [],
    "overallScore": None,
    "conclusion": "success",
}


class _VisibilityApi:
    def __init__(self):
        self.calls = []

    def _request(self, method, path, *, token=None, body=None, **kwargs):  # noqa: ARG002
        self.calls.append((method, path, token, body))
        if path == "/repos/example/private-control/installation":
            return {"id": 99}
        if path == "/app/installations/99/access_tokens":
            return {"token": "related-token"}
        if path == "/repos/example/private-control":
            # Trigger repository is private; this candidate is deliberately public.
            return {"default_branch": "main", "visibility": "public", "private": False}
        raise AssertionError(f"unexpected API request: {method} {path}")

    def repository_tarball(self, token, repository, revision):  # pragma: no cover
        raise AssertionError("visibility-mismatched repository must never be downloaded")


class ProductVisibilityBoundaryTests(unittest.TestCase):
    def test_visibility_is_checked_before_related_manifest_is_read(self):
        api = _VisibilityApi()

        def trusted_manifest(_api, _token, repository, *, metadata=None):
            if repository == "example/contracts":
                self.assertIsNone(metadata)
                return MANIFEST, {"default_branch": "main", "visibility": "private", "private": True}
            self.fail("related trusted manifest must not be read across the visibility boundary")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch("iaap_guard.github_product_scope._trusted_manifest", side_effect=trusted_manifest):
                assessment, _ = evaluate_trusted_product_scope(
                    api=api,
                    app_jwt="app-jwt",
                    trigger_token="trigger-token",
                    trigger_repository="example/contracts",
                    trigger_root=root,
                    trigger_result=TRIGGER_RESULT,
                    extract_archive=lambda _archive, destination: destination,
                )

        self.assertEqual(assessment["conclusion"], "incomplete")
        self.assertFalse(assessment["acquisition"]["relatedRepositoryContentRead"])
        self.assertEqual(assessment["completeness"]["missingRequired"], ["example/private-control"])
        self.assertFalse(any("/contents/.iaap/product.yaml" in call[1] for call in api.calls))


if __name__ == "__main__":
    unittest.main()
