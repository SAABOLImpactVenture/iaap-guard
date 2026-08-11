from __future__ import annotations

import unittest

from iaap_guard.github_app import PullRequestTarget
from iaap_guard.github_beta_runtime import BetaGitHubApi, render_beta_check_output


def _result(findings, *, conclusion="failure", score=50):
    return {
        "schemaVersion": "scan-result/v1",
        "ruleCatalogVersion": "iaap-guard/v0.1.2",
        "scoringModelVersion": "coverage/v1",
        "repository": {"name": "example/platform"},
        "revision": {"sha": "b" * 40},
        "detectedComponents": ["consumer-contract"],
        "findings": findings,
        "ruleResults": [],
        "dimensionScores": [
            {"dimension": "Product Abstraction", "passed": 0, "applicable": 0, "score": None},
            {"dimension": "Consumer Boundary", "passed": 1, "applicable": 2, "score": score},
            {"dimension": "Experience / Authority", "passed": 0, "applicable": 0, "score": None},
            {"dimension": "Control-Plane Separation", "passed": 0, "applicable": 0, "score": None},
            {"dimension": "Governance", "passed": 0, "applicable": 0, "score": None},
            {"dimension": "Evidence Readiness", "passed": 0, "applicable": 0, "score": None},
        ],
        "overallScore": score,
        "conclusion": conclusion,
    }


class Phase11GitHubPlanningTests(unittest.TestCase):
    def test_check_with_findings_includes_compact_improvement_plan(self):
        finding = {
            "ruleId": "IAP-P001",
            "result": "FAIL",
            "dimension": "Consumer Boundary",
            "componentContext": "consumer-contract",
            "path": "product/schema.yaml",
            "line": 12,
            "evidence": "consumer-facing field exposes implementation machinery",
            "recommendation": "Move implementation selection behind the stable product contract.",
            "scoring": True,
            "experimental": False,
        }
        output = render_beta_check_output(_result([finding]))
        self.assertIn("Improvement Plan", output["text"])
        self.assertIn("O1", output["text"])
        self.assertIn("O1-KR1", output["text"])
        self.assertIn("O1-E1", output["text"])
        self.assertIn("Candidate User Story", output["text"])
        self.assertIn("Candidate tasks", output["text"])
        self.assertIn("product/schema.yaml:12", output["text"])
        self.assertIn("Improvement plan:", output["summary"])

    def test_check_without_findings_does_not_invent_backlog(self):
        output = render_beta_check_output(_result([], conclusion="success", score=100))
        self.assertNotIn("Improvement Plan", output["text"])
        self.assertIn("No WARNING or FAIL findings", output["text"])
        self.assertNotIn("Improvement plan:", output["summary"])

    def test_no_relevant_change_does_not_create_planning_work(self):
        output = render_beta_check_output(
            _result([], conclusion="success", score=None),
            no_relevant_changes=True,
        )
        self.assertNotIn("Improvement Plan", output["text"])
        self.assertIn("No changed file matched", output["text"])

    def test_beta_api_publishes_planning_output_through_check_run(self):
        class RecordingApi(BetaGitHubApi):
            def __init__(self):
                super().__init__()
                self.call = None

            def check_runs_for_revision(self, token, repository, revision):  # noqa: ARG002
                return []

            def _request(self, method, path, **kwargs):
                self.call = (method, path, kwargs.get("body"))
                return {"id": 101}

        finding = {
            "ruleId": "IAP-P001",
            "result": "FAIL",
            "dimension": "Consumer Boundary",
            "componentContext": "consumer-contract",
            "path": "product/schema.yaml",
            "evidence": "implementation machinery exposed",
            "recommendation": "Hide implementation machinery.",
            "scoring": True,
            "experimental": False,
        }
        api = RecordingApi()
        target = PullRequestTarget(
            "example/platform",
            1,
            17,
            "b" * 40,
            2,
            "refs/pull/17/head",
        )
        api.upsert_check_run("token", target, _result([finding]), no_relevant_changes=False)
        self.assertEqual(api.call[0], "POST")
        self.assertIn("Improvement Plan", api.call[2]["output"]["text"])
        self.assertEqual(api.call[2]["name"], "IaaP Guard / Architecture")
        self.assertEqual(api.call[2]["conclusion"], "failure")


if __name__ == "__main__":
    unittest.main()
