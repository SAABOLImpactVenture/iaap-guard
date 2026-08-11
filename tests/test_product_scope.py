from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from iaap_guard.product import build_product_assessment
from iaap_guard.product_planning import build_product_planning_report, render_product_planning_markdown

ROOT = Path(__file__).resolve().parents[1]


def _manifest(required_second=True):
    return {
        "schemaVersion": "iaap-product/v1",
        "product": {"id": "cloud-foundation", "name": "Cloud Foundation", "owner": "platform-team"},
        "repositories": [
            {
                "name": "example/contracts",
                "roles": ["product-contract"],
                "required": True,
                "primary": True,
            },
            {
                "name": "example/control-plane",
                "roles": ["control-plane", "evidence"],
                "required": required_second,
            },
        ],
    }


def _result(name, *, score=100, conclusion="success", finding=None, rule_version="iaap-guard/v0.1.2"):
    applicable = 1
    passed = 1 if score == 100 else 0
    findings = [finding] if finding else []
    return {
        "schemaVersion": "scan-result/v1",
        "ruleCatalogVersion": rule_version,
        "scoringModelVersion": "coverage/v1",
        "repository": {"name": name},
        "revision": {"sha": ("a" if "contracts" in name else "b") * 40},
        "detectedComponents": [],
        "findings": findings,
        "ruleResults": [],
        "dimensionScores": [
            {"dimension": "Product Abstraction", "passed": passed, "applicable": applicable, "score": score},
            {"dimension": "Consumer Boundary", "passed": passed, "applicable": applicable, "score": score},
            {"dimension": "Experience / Authority", "passed": 0, "applicable": 0, "score": None},
            {"dimension": "Control-Plane Separation", "passed": 0, "applicable": 0, "score": None},
            {"dimension": "Governance", "passed": 0, "applicable": 0, "score": None},
            {"dimension": "Evidence Readiness", "passed": 0, "applicable": 0, "score": None},
        ],
        "overallScore": score,
        "conclusion": conclusion,
    }


def _validate_schema(filename: str, instance: dict) -> None:
    schema = json.loads((ROOT / "schemas" / filename).read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(instance)


class ProductScopeTests(unittest.TestCase):
    def test_complete_product_aggregates_member_evidence(self):
        assessment = build_product_assessment(
            _manifest(),
            [_result("example/contracts"), _result("example/control-plane")],
        )
        self.assertEqual(assessment["schemaVersion"], "product-assessment/v1")
        self.assertEqual(assessment["conclusion"], "success")
        self.assertTrue(assessment["completeness"]["complete"])
        self.assertEqual(assessment["overallScore"], 100)
        self.assertEqual(assessment["minimumMemberScore"], 100)
        self.assertEqual(assessment["completeness"]["present"], 2)
        self.assertEqual(assessment["acquisition"]["mode"], "provided-evidence")
        self.assertFalse(assessment["acquisition"]["relatedRepositoryContentRead"])
        self.assertEqual(assessment["relationshipEvaluation"]["status"], "not-evaluated")
        self.assertTrue(assessment["boundary"]["memberFailureCannotBeAveragedAway"])
        _validate_schema("product-assessment.schema.json", assessment)

    def test_member_failure_cannot_be_averaged_away(self):
        finding = {
            "ruleId": "IAP-P001",
            "result": "FAIL",
            "dimension": "Consumer Boundary",
            "componentContext": "consumer-contract",
            "path": "product/schema.yaml",
            "line": 9,
            "evidence": "consumer-facing contract exposes implementation machinery",
            "recommendation": "Move implementation selection behind the product boundary.",
            "scoring": True,
            "experimental": False,
        }
        assessment = build_product_assessment(
            _manifest(),
            [
                _result("example/contracts", score=0, conclusion="failure", finding=finding),
                _result("example/control-plane", score=100, conclusion="success"),
            ],
        )
        self.assertEqual(assessment["conclusion"], "failure")
        self.assertEqual(assessment["minimumMemberScore"], 0)
        self.assertEqual(assessment["findings"][0]["repository"], "example/contracts")

    def test_missing_required_member_is_incomplete_not_silently_green(self):
        assessment = build_product_assessment(_manifest(), [_result("example/contracts")])
        self.assertEqual(assessment["conclusion"], "incomplete")
        self.assertFalse(assessment["completeness"]["complete"])
        self.assertEqual(assessment["completeness"]["missingRequired"], ["example/control-plane"])
        self.assertTrue(any(item["ruleId"] == "IAP-PR001" for item in assessment["findings"]))
        _validate_schema("product-assessment.schema.json", assessment)

    def test_missing_optional_member_does_not_make_product_incomplete(self):
        assessment = build_product_assessment(_manifest(required_second=False), [_result("example/contracts")])
        self.assertEqual(assessment["conclusion"], "success")
        self.assertTrue(assessment["completeness"]["complete"])

    def test_mixed_rule_versions_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "different rule catalog versions"):
            build_product_assessment(
                _manifest(),
                [
                    _result("example/contracts", rule_version="iaap-guard/v0.1.2"),
                    _result("example/control-plane", rule_version="iaap-guard/v9"),
                ],
            )

    def test_product_plan_retains_member_traceability(self):
        finding = {
            "ruleId": "IAP-P001",
            "result": "FAIL",
            "dimension": "Consumer Boundary",
            "componentContext": "consumer-contract",
            "path": "product/schema.yaml",
            "line": 12,
            "evidence": "consumer-facing field exposes implementation machinery",
            "recommendation": "Hide implementation machinery.",
            "scoring": True,
            "experimental": False,
        }
        assessment = build_product_assessment(
            _manifest(),
            [
                _result("example/contracts", score=0, conclusion="failure", finding=finding),
                _result("example/control-plane"),
            ],
        )
        report = build_product_planning_report(assessment)
        self.assertEqual(report["schemaVersion"], "product-planning-report/v1")
        self.assertGreater(report["totals"]["epics"], 0)
        self.assertTrue(report["boundary"]["doesNotExpandGitHubAppPermissions"])
        self.assertEqual(report["source"]["acquisitionMode"], "provided-evidence")
        self.assertEqual(report["source"]["relationshipEvaluationStatus"], "not-evaluated")
        _validate_schema("product-planning-report.schema.json", report)
        markdown = render_product_planning_markdown(report)
        self.assertIn("example/contracts:product/schema.yaml:12", markdown)
        self.assertIn("Key Results", markdown)
        self.assertIn("Candidate User Story", markdown)


if __name__ == "__main__":
    unittest.main()
