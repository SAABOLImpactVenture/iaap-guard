from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "artifacts" / "phase-9"


class Phase9EvidenceTests(unittest.TestCase):
    def load(self, name: str):
        return json.loads((EVIDENCE / name).read_text(encoding="utf-8"))

    def test_portfolio_closeout_evidence(self):
        baseline = self.load("portfolio-baseline.json")
        expected = self.load("expected-vs-actual.json")
        false_positive = self.load("false-positive-analysis.json")
        mutation = self.load("mutation-matrix.json")
        repeatability = self.load("repeatability.json")
        scorecard = self.load("dogfood-scorecard.json")
        index = self.load("index.json")

        self.assertEqual(baseline["ruleCatalogVersion"], "iaap-guard/v0.1.2")
        self.assertEqual(baseline["scoringModelVersion"], "coverage/v1")
        self.assertEqual(len(baseline["repositories"]), 6)

        result_paths = sorted((EVIDENCE / "repository-results").glob("*.json"))
        self.assertEqual(len(result_paths), 6)
        for path in result_paths:
            result = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(result["ruleCatalogVersion"], "iaap-guard/v0.1.2")
            self.assertEqual(result["scoringModelVersion"], "coverage/v1")
            self.assertEqual(result["conclusion"], "success")
            self.assertEqual(result["overallScore"], 100)
            self.assertEqual(result["findings"], [])
            self.assertRegex(result["revision"]["sha"], r"^[0-9a-f]{40}$")

        self.assertEqual(expected["summary"], {"matched": 6, "total": 6})
        self.assertEqual(false_positive["finalCriticalFalseFailures"], 0)
        self.assertEqual(mutation["criticalRulesDetected"], mutation["criticalRulesTotal"])
        self.assertTrue(mutation["allMutationFixturesExact"])
        self.assertTrue(all(item["detected"] and item["actual"] == "FAIL" for item in mutation["mutations"]))
        self.assertEqual(repeatability["summary"]["byteIdentical"], 6)
        self.assertEqual(repeatability["summary"]["semanticIdentical"], 6)
        self.assertTrue(repeatability["summary"]["passed"])
        self.assertEqual(scorecard["exitGate"], "PASS")
        self.assertTrue(all(item["result"] == "PASS" for item in scorecard["criteria"]))
        self.assertEqual(index["exitGate"], "PASS")


if __name__ == "__main__":
    unittest.main()
