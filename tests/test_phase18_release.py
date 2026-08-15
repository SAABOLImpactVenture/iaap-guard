import unittest
from pathlib import Path

import iaap_guard


ROOT = Path(__file__).resolve().parents[1]


class Phase18ReleaseTests(unittest.TestCase):
    def test_product_version_is_v1(self):
        self.assertEqual(iaap_guard.__version__, "1.0.0")

    def test_release_policies_exist_and_preserve_boundary(self):
        for relative in (
            "CHANGELOG.md",
            "docs/SUPPORT.md",
            "docs/UPGRADING.md",
            "docs/KNOWN-LIMITS.md",
            "docs/V1-CONTRACT-FREEZE.md",
            "docs/PHASE-18-VALIDATION.md",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertTrue(text.strip(), relative)

        limits = (ROOT / "docs/KNOWN-LIMITS.md").read_text(encoding="utf-8")
        self.assertIn("does not ingest organizational OKRs", limits)
        self.assertIn("execute infrastructure", limits)
        self.assertIn("mutate repositories", limits)

    def test_completion_status_is_consistent(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        architecture = (ROOT / "docs/ARCHITECTURE.md").read_text(encoding="utf-8")
        plan = (ROOT / "planning/phase-18.md").read_text(encoding="utf-8")

        self.assertIn("PHASE 18 — V1 Product Completion: COMPLETE", readme)
        self.assertIn("Phase 18 — V1 Product Completion — COMPLETE", architecture)
        self.assertIn("**COMPLETE**", plan)
        self.assertNotIn("Phase 18 — V1 Product Completion — PLANNED", architecture)


if __name__ == "__main__":
    unittest.main()
