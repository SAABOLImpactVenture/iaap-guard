from __future__ import annotations

import unittest
from pathlib import Path

import yaml

from iaap_guard.scanner import scan_path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = yaml.safe_load((ROOT / "fixtures/expected-results.yaml").read_text(encoding="utf-8"))
REVISION = "1" * 40


class FixtureContractTests(unittest.TestCase):
    def test_all_frozen_fixture_expectations(self):
        for case in EXPECTED["cases"]:
            with self.subTest(case=case["path"]):
                result = scan_path(
                    ROOT / "fixtures" / case["path"],
                    repository=f"fixture:{case['path']}",
                    revision=REVISION,
                    ref="fixture",
                )
                actual = {item["ruleId"]: item["result"] for item in result["ruleResults"]}
                for rule_id, expected_result in case.get("expected", {}).items():
                    self.assertEqual(actual[rule_id], expected_result)

                if case.get("expectedCriticalFailures") == 0:
                    critical = [
                        item for item in result["ruleResults"]
                        if item["scoring"] and item["result"] == "FAIL"
                    ]
                    self.assertEqual(critical, [])

    def test_consumer_leakage_has_file_evidence(self):
        result = scan_path(
            ROOT / "fixtures/negative/consumer-providerconfig.yaml",
            repository="fixture",
            revision=REVISION,
        )
        finding = next(item for item in result["findings"] if item["ruleId"] == "IAP-P001")
        self.assertEqual(finding["componentContext"], "consumer-contract")
        self.assertGreaterEqual(finding.get("line", 0), 1)
        self.assertIn("providerConfig", finding["evidence"])

    def test_implementation_providerconfig_is_not_consumer_leakage(self):
        result = scan_path(
            ROOT / "fixtures/good/providerconfig-behind-implementation.yaml",
            repository="fixture",
            revision=REVISION,
        )
        actual = {item["ruleId"]: item["result"] for item in result["ruleResults"]}
        self.assertEqual(actual["IAP-P001"], "NOT_APPLICABLE")
        self.assertFalse(any(item["ruleId"] == "IAP-P001" for item in result["findings"]))

    def test_ai_deny_list_does_not_grant_authority(self):
        result = scan_path(
            ROOT / "fixtures/good/ai-denylist.json",
            repository="fixture",
            revision=REVISION,
        )
        actual = {item["ruleId"]: item["result"] for item in result["ruleResults"]}
        self.assertEqual(actual["IAP-A001"], "PASS")
        self.assertEqual(actual["IAP-A002"], "PASS")


if __name__ == "__main__":
    unittest.main()
