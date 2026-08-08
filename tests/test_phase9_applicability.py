from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from iaap_guard.scanner import scan_path

REVISION = "3" * 40


class Phase9ApplicabilityTests(unittest.TestCase):
    def test_evidence_only_repository_does_not_acquire_lifecycle_obligation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workflow = root / ".github/workflows/validate.yml"
            workflow.parent.mkdir(parents=True)
            workflow.write_text(
                "name: validate\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - run: make validate\n",
                encoding="utf-8",
            )

            result = scan_path(
                root,
                repository="evidence-only",
                revision=REVISION,
            )

        e001 = next(item for item in result["ruleResults"] if item["ruleId"] == "IAP-E001")
        self.assertEqual(e001["result"], "NOT_APPLICABLE")
        self.assertFalse(any(finding["ruleId"] == "IAP-E001" for finding in result["findings"]))

    def test_consumer_contract_without_control_plane_does_not_acquire_lifecycle_obligation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract = root / "api/product-contract.yaml"
            contract.parent.mkdir(parents=True)
            contract.write_text(
                "apiVersion: platform.example/v1\n"
                "kind: InfrastructureProductSchema\n"
                "spec:\n"
                "  required: [owner]\n"
                "  properties:\n"
                "    owner:\n"
                "      type: string\n",
                encoding="utf-8",
            )

            result = scan_path(
                root,
                repository="consumer-only",
                revision=REVISION,
            )

        self.assertIn("consumer-contract", result["detectedComponents"])
        self.assertNotIn("control-plane-implementation", result["detectedComponents"])
        e001 = next(item for item in result["ruleResults"] if item["ruleId"] == "IAP-E001")
        self.assertEqual(e001["result"], "NOT_APPLICABLE")
        self.assertFalse(any(finding["ruleId"] == "IAP-E001" for finding in result["findings"]))


if __name__ == "__main__":
    unittest.main()
