from __future__ import annotations

import unittest

from iaap_guard.planning import build_planning_report, render_planning_markdown


def _scan_result(findings):
    return {
        "schemaVersion": "scan-result/v1",
        "ruleCatalogVersion": "iaap-guard/v0.1.2",
        "scoringModelVersion": "coverage/v1",
        "repository": {"name": "example/platform"},
        "revision": {"sha": "a" * 40},
        "detectedComponents": ["consumer-contract", "experience"],
        "findings": findings,
        "ruleResults": [],
        "dimensionScores": [
            {"dimension": "Product Abstraction", "passed": 1, "applicable": 1, "score": 100},
            {"dimension": "Consumer Boundary", "passed": 1, "applicable": 2, "score": 50},
            {"dimension": "Experience / Authority", "passed": 0, "applicable": 1, "score": 0},
            {"dimension": "Control-Plane Separation", "passed": 0, "applicable": 0, "score": None},
            {"dimension": "Governance", "passed": 0, "applicable": 0, "score": None},
            {"dimension": "Evidence Readiness", "passed": 0, "applicable": 0, "score": None},
        ],
        "overallScore": 50,
        "conclusion": "failure" if any(item["result"] == "FAIL" for item in findings) else "neutral",
    }


class PlanningReportTests(unittest.TestCase):
    def test_finding_becomes_okr_epic_feature_story_and_tasks(self):
        finding = {
            "ruleId": "IAP-P001",
            "result": "FAIL",
            "dimension": "Consumer Boundary",
            "componentContext": "consumer-contract",
            "path": "product/schema.yaml",
            "line": 12,
            "evidence": "consumer-facing field 'ProviderConfig' exposes implementation machinery",
            "recommendation": "Move implementation selection behind the stable infrastructure product contract.",
            "scoring": True,
            "experimental": False,
        }
        report = build_planning_report(_scan_result([finding]))

        self.assertEqual(report["schemaVersion"], "planning-report/v1")
        self.assertEqual(report["planningCatalogVersion"], "iaap-planning/v0.1.0")
        self.assertEqual(report["status"], "improvement-required")
        self.assertEqual(report["totals"]["objectives"], 1)
        self.assertEqual(report["totals"]["epics"], 1)
        self.assertEqual(report["totals"]["features"], 1)
        self.assertEqual(report["totals"]["userStories"], 1)
        self.assertGreater(report["totals"]["candidateTasks"], 0)

        objective = report["objectives"][0]
        self.assertEqual(objective["id"], "O1")
        self.assertEqual(objective["dimension"], "Consumer Boundary")
        self.assertEqual(objective["baselineScore"], 50)
        self.assertEqual(objective["targetScore"], 100)
        self.assertGreaterEqual(len(objective["keyResults"]), 2)

        epic = objective["epics"][0]
        self.assertEqual(epic["ruleId"], "IAP-P001")
        self.assertTrue(epic["keyResultIds"])
        self.assertEqual(epic["evidence"][0]["path"], "product/schema.yaml")
        self.assertEqual(epic["evidence"][0]["line"], 12)

        feature = epic["features"][0]
        story = feature["userStories"][0]
        self.assertTrue(story["candidate"])
        self.assertIn("As a application team", story["statement"])
        self.assertTrue(story["acceptanceEvidence"])
        self.assertTrue(all(task["candidate"] for task in story["candidateTasks"]))

    def test_repeated_rule_findings_group_into_one_epic(self):
        findings = [
            {
                "ruleId": "IAP-P001",
                "result": "FAIL",
                "dimension": "Consumer Boundary",
                "componentContext": "consumer-contract",
                "path": path,
                "evidence": "implementation field exposed",
                "recommendation": "Hide implementation machinery.",
                "scoring": True,
                "experimental": False,
            }
            for path in ("product/a.yaml", "product/b.yaml")
        ]
        report = build_planning_report(_scan_result(findings))
        objective = report["objectives"][0]
        self.assertEqual(len(objective["epics"]), 1)
        self.assertEqual(objective["epics"][0]["findingCount"], 2)
        self.assertEqual(len(objective["epics"][0]["evidence"]), 2)
        self.assertTrue(any(kr["metric"] == "blockingGuardFindings" for kr in objective["keyResults"]))

    def test_no_findings_produces_no_backlog(self):
        result = _scan_result([])
        result["conclusion"] = "success"
        result["overallScore"] = 100
        report = build_planning_report(result)
        self.assertEqual(report["status"], "no-current-findings")
        self.assertEqual(report["objectives"], [])
        self.assertEqual(report["totals"]["candidateTasks"], 0)
        self.assertTrue(report["boundary"]["candidateBacklogOnly"])
        self.assertTrue(report["boundary"]["doesNotManageSprints"])

    def test_markdown_preserves_traceability_and_product_boundary(self):
        finding = {
            "ruleId": "IAP-X001",
            "result": "FAIL",
            "dimension": "Experience / Authority",
            "componentContext": "experience",
            "path": "templates/order.yaml",
            "line": 7,
            "evidence": "experience action directly executes infrastructure",
            "recommendation": "Submit bounded product intent instead.",
            "scoring": True,
            "experimental": False,
        }
        markdown = render_planning_markdown(build_planning_report(_scan_result([finding])))
        self.assertIn("IaaP Guard Improvement Plan", markdown)
        self.assertIn("### Key Results", markdown)
        self.assertIn("Candidate User Story", markdown)
        self.assertIn("Candidate tasks", markdown)
        self.assertIn("templates/order.yaml:7", markdown)
        self.assertIn("not execution commitments", markdown)


if __name__ == "__main__":
    unittest.main()
