from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from jsonschema.validators import validator_for

from iaap_guard.scanner import scan_path
from iaap_guard.scoring import score_results

ROOT = Path(__file__).resolve().parents[1]
REVISION = "2" * 40


class DeterministicCoreTests(unittest.TestCase):
    def test_scan_result_matches_published_schema(self):
        result = scan_path(
            ROOT / "fixtures/negative/storefront-domain-broader.yaml",
            repository="fixture",
            revision=REVISION,
            ref="test",
        )
        schema = json.loads((ROOT / "schemas/scan-result.schema.json").read_text(encoding="utf-8"))
        validator_cls = validator_for(schema)
        validator_cls.check_schema(schema)
        validator_cls(schema).validate(result)

    def test_repeatability(self):
        target = ROOT / "fixtures/negative/consumer-lifecycle-policy.yaml"
        first = scan_path(target, repository="fixture", revision=REVISION)
        second = scan_path(target, repository="fixture", revision=REVISION)
        self.assertEqual(first, second)

    def test_scanner_does_not_execute_repository_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sentinel = root / "executed.txt"
            (root / "malicious.py").write_text(
                f"from pathlib import Path\nPath({str(sentinel)!r}).write_text('executed')\n",
                encoding="utf-8",
            )
            scan_path(root, repository="untrusted", revision=REVISION)
            self.assertFalse(sentinel.exists())

    def test_repository_scan_does_not_promote_negative_fixtures_to_live_architecture(self):
        result = scan_path(ROOT, repository="iaap-guard", revision=REVISION)
        fixture_failures = [
            finding
            for finding in result["findings"]
            if finding["result"] == "FAIL" and finding["path"].startswith("fixtures/")
        ]
        self.assertEqual(fixture_failures, [])

    def test_experimental_warning_does_not_affect_score_or_conclusion(self):
        dimension_scores, overall, conclusion = score_results(
            [
                {
                    "ruleId": "IAP-CX01",
                    "result": "WARNING",
                    "dimension": "Control-Plane Separation",
                    "scoring": False,
                    "experimental": True,
                }
            ],
            ["Control-Plane Separation"],
        )
        self.assertIsNone(overall)
        self.assertEqual(conclusion, "success")
        self.assertEqual(dimension_scores[0]["applicable"], 0)

    def test_warning_is_neutral_and_fail_is_failure(self):
        warning = [{"ruleId": "x", "result": "WARNING", "dimension": "Governance", "scoring": True, "experimental": False}]
        failure = [{"ruleId": "x", "result": "FAIL", "dimension": "Governance", "scoring": True, "experimental": False}]
        self.assertEqual(score_results(warning, ["Governance"])[2], "neutral")
        self.assertEqual(score_results(failure, ["Governance"])[2], "failure")

    def test_not_applicable_is_excluded_from_score(self):
        results = [
            {"ruleId": "a", "result": "PASS", "dimension": "Governance", "scoring": True, "experimental": False},
            {"ruleId": "b", "result": "NOT_APPLICABLE", "dimension": "Governance", "scoring": True, "experimental": False},
        ]
        dimensions, overall, conclusion = score_results(results, ["Governance"])
        self.assertEqual(dimensions[0], {"dimension": "Governance", "passed": 1, "applicable": 1, "score": 100})
        self.assertEqual(overall, 100)
        self.assertEqual(conclusion, "success")

    def test_revision_must_be_immutable_sha_shape(self):
        with self.assertRaises(ValueError):
            scan_path(ROOT / "fixtures/good/product-contract.yaml", repository="fixture", revision="main")


if __name__ == "__main__":
    unittest.main()
