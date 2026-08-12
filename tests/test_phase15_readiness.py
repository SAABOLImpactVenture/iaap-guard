from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import yaml
from jsonschema.validators import validator_for

from iaap_guard.github_app import PullRequestTarget, _safe_extract_tarball
from iaap_guard.github_product_runtime import _append_readiness_output, _replace_check_output
from iaap_guard.github_product_scope import evaluate_trusted_product_scope
from iaap_guard.readiness import evaluate_repository_readiness
from tests.test_product_github_scope import _ProductApi, _manifest, _trigger_result, _trigger_root

ROOT = Path(__file__).resolve().parents[1]


def _write_manifest(root: Path, manifest: dict) -> None:
    path = root / ".iaap/product.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")


def _github_readiness(api):
    with _trigger_root() as root:
        return evaluate_trusted_product_scope(
            api=api,
            app_jwt="app-jwt",
            trigger_token="trigger-token",
            trigger_repository="example/contracts",
            trigger_root=root,
            trigger_result=_trigger_result(),
            extract_archive=_safe_extract_tarball,
            include_readiness=True,
        )


class Phase15LocalReadinessTests(unittest.TestCase):
    def test_single_repository_without_manifest_is_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "product.yaml").write_text("apiVersion: platform.example/v1\nkind: InfrastructureProductSchema\n", encoding="utf-8")
            report = evaluate_repository_readiness(root, repository="example/product")
        self.assertEqual(report["overallStatus"], "READY")
        registration = next(item for item in report["requirements"] if item["id"] == "IAP-RDY005")
        self.assertEqual(registration["status"], "NOT_APPLICABLE")

    def test_no_supported_artifacts_is_advisory(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = evaluate_repository_readiness(tmp, repository="example/empty")
        self.assertEqual(report["overallStatus"], "READY_WITH_ADVISORIES")
        self.assertFalse(report["blockingRequirements"])

    def test_malformed_manifest_is_actionable_blocker(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".iaap/product.yaml"
            path.parent.mkdir(parents=True)
            path.write_text("schemaVersion: wrong\n", encoding="utf-8")
            report = evaluate_repository_readiness(tmp, repository="example/product")
        self.assertEqual(report["overallStatus"], "BLOCKED")
        self.assertIn("iaap-product/v1", next(item for item in report["requirements"] if item["id"] == "IAP-RDY005")["remediation"])

    def test_missing_trigger_duplicate_oversized_and_multiple_primary_are_blocked(self):
        base = _manifest()
        cases = []
        cases.append(base)
        duplicate = _manifest(); duplicate["repositories"].append(dict(duplicate["repositories"][1])); cases.append(duplicate)
        oversized = _manifest(); oversized["repositories"] = [{"name": f"example/r{i}", "roles": ["other"]} for i in range(13)]; cases.append(oversized)
        primaries = _manifest(); primaries["repositories"][1]["primary"] = True; cases.append(primaries)
        for index, manifest in enumerate(cases):
            with self.subTest(index=index), tempfile.TemporaryDirectory() as tmp:
                _write_manifest(Path(tmp), manifest)
                repository = "example/missing" if index == 0 else "example/contracts"
                report = evaluate_repository_readiness(tmp, repository=repository)
                self.assertEqual(report["overallStatus"], "BLOCKED")

    def test_valid_local_product_is_ready_with_github_checks_explicitly_advisory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_manifest(root, _manifest())
            (root / "contract.yaml").write_text("apiVersion: platform.example/v1\nkind: InfrastructureProductSchema\n", encoding="utf-8")
            report = evaluate_repository_readiness(root, repository="example/contracts")
        self.assertEqual(report["scope"]["mode"], "product")
        self.assertEqual(report["overallStatus"], "READY")
        github_only = next(item for item in report["requirements"] if item["id"] == "IAP-RDY007")
        self.assertEqual(github_only["status"], "NOT_APPLICABLE")
        schema = json.loads((ROOT / "schemas/readiness-report.schema.json").read_text(encoding="utf-8"))
        validator_for(schema)(schema).validate(report)


class Phase15GitHubReadinessTests(unittest.TestCase):
    def test_all_required_members_ready(self):
        assessment, plan, readiness = _github_readiness(_ProductApi(_manifest()))
        self.assertIsNotNone(assessment); self.assertIsNotNone(plan)
        self.assertEqual(readiness["overallStatus"], "READY")
        self.assertEqual(readiness["summary"]["blocked"], 0)

    def test_visibility_and_reciprocity_have_precise_blockers(self):
        visibility = _github_readiness(_ProductApi(_manifest(), related_visibility="public"))[2]
        self.assertEqual(visibility["overallStatus"], "BLOCKED")
        self.assertIn("IAP-RDY103", visibility["blockingRequirements"])
        other = _manifest(); other["product"]["id"] = "other"
        reciprocal = _github_readiness(_ProductApi(_manifest(), related_manifest=other))[2]
        self.assertIn("IAP-RDY106", reciprocal["blockingRequirements"])

    def test_missing_manifest_and_inaccessible_member_are_blocked(self):
        class MissingManifest(_ProductApi):
            def _request(self, method, path, **kwargs):
                if path.startswith(f"/repos/{self.related_repository}/contents/.iaap/product.yaml"):
                    raise RuntimeError("GitHub API HTTP 404")
                return super()._request(method, path, **kwargs)
        missing = _github_readiness(MissingManifest(_manifest()))[2]
        self.assertIn("IAP-RDY105", missing["blockingRequirements"])

        class Inaccessible(_ProductApi):
            def _request(self, method, path, **kwargs):
                if path == f"/repos/{self.related_repository}/installation":
                    raise RuntimeError("GitHub API HTTP 404")
                return super()._request(method, path, **kwargs)
        inaccessible = _github_readiness(Inaccessible(_manifest()))[2]
        blocker = next(item for item in inaccessible["requirements"] if item["id"] == "IAP-RDY104")
        self.assertIn("No new permission type", blocker["remediation"])

    def test_optional_unavailable_member_is_advisory(self):
        manifest = _manifest(); manifest["repositories"][1]["required"] = False
        other = _manifest(); other["repositories"][1]["required"] = False; other["product"]["id"] = "other"
        readiness = _github_readiness(_ProductApi(manifest, related_manifest=other))[2]
        self.assertEqual(readiness["overallStatus"], "READY_WITH_ADVISORIES")
        self.assertFalse(readiness["blockingRequirements"])

    def test_rendering_keeps_continuity_and_check_conclusion(self):
        _, _, readiness = _github_readiness(_ProductApi(_manifest()))
        output = {"summary": "Evidence continuity: **SUPPORTED**.", "text": "Evidence continuity is not authorization continuity."}
        rendered = _append_readiness_output(output, readiness)
        self.assertIn("SUPPORTED", rendered["summary"])
        self.assertIn("Product Readiness", rendered["summary"])
        self.assertIn("Evidence continuity is not authorization continuity", rendered["text"])

        class CheckApi:
            payload = None
            def check_runs_for_revision(self, token, repository, revision):  # noqa: ARG002
                return []
            def _request(self, method, path, *, token=None, body=None):  # noqa: ARG002
                self.payload = body
                return {"id": 1}
        api = CheckApi()
        target = PullRequestTarget("example/contracts", 1, 7, "a" * 40, 2, "refs/pull/7/head")
        _replace_check_output(api, "token", target, {"conclusion": "neutral"}, rendered)
        self.assertEqual(api.payload["conclusion"], "neutral")
