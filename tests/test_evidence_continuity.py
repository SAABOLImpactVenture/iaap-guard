from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from jsonschema.validators import validator_for

from iaap_guard.evidence import build_evidence_manifest, render_evidence_markdown
from iaap_guard.scanner import scan_path

ROOT = Path(__file__).resolve().parents[1]
BASELINE_REVISION = "1" * 40
CURRENT_REVISION = "2" * 40


class EvidenceContinuityTests(unittest.TestCase):
    def _good_scan(self, revision: str = BASELINE_REVISION) -> dict:
        return scan_path(
            ROOT / "fixtures/good/product-contract.yaml",
            repository="example/platform-product",
            revision=revision,
        )

    def _negative_scan(self) -> dict:
        return scan_path(
            ROOT / "fixtures/negative/storefront-domain-broader.yaml",
            repository="example/platform-product",
            revision=CURRENT_REVISION,
        )

    def test_manifest_matches_published_schema(self):
        baseline = self._good_scan()
        current = copy.deepcopy(baseline)
        current["revision"] = {"sha": CURRENT_REVISION}
        manifest = build_evidence_manifest(current, baseline)

        schema = json.loads((ROOT / "schemas/evidence-manifest.schema.json").read_text(encoding="utf-8"))
        validator_cls = validator_for(schema)
        validator_cls.check_schema(schema)
        validator_cls(schema).validate(manifest)

    def test_without_baseline_manifest_is_anchor_not_authorization(self):
        manifest = build_evidence_manifest(self._good_scan(), None)
        self.assertEqual(manifest["evidenceContinuity"]["status"], "not_established")
        self.assertEqual(manifest["disposition"]["status"], "baseline_required")
        self.assertEqual(manifest["changeAssessment"]["materiality"], "unknown_without_baseline")
        self.assertFalse(manifest["boundary"]["authorizationDetermination"])
        self.assertEqual(manifest["authorityEvidence"]["status"], "not_determined")

    def test_revalidated_same_guard_state_supports_continuity(self):
        baseline = self._good_scan()
        current = copy.deepcopy(baseline)
        current["revision"] = {"sha": CURRENT_REVISION}

        manifest = build_evidence_manifest(current, baseline)
        self.assertTrue(manifest["changeAssessment"]["sourceStateChanged"])
        self.assertTrue(manifest["changeAssessment"]["evidenceChanged"])
        self.assertEqual(
            manifest["changeAssessment"]["materiality"],
            "no_guard_material_change_detected",
        )
        self.assertEqual(manifest["evidenceContinuity"]["status"], "supported")
        self.assertEqual(manifest["disposition"]["status"], "no_additional_guard_review")
        self.assertIn(
            "current_state_revalidated_without_guard_material_change",
            manifest["evidenceContinuity"]["reasons"],
        )

    def test_rule_or_finding_change_requires_human_review(self):
        manifest = build_evidence_manifest(self._negative_scan(), self._good_scan())
        self.assertEqual(manifest["evidenceContinuity"]["status"], "review_required")
        self.assertEqual(manifest["disposition"]["status"], "human_review_required")
        self.assertEqual(
            manifest["changeAssessment"]["materiality"],
            "guard_material_change_detected",
        )
        self.assertTrue(
            manifest["changeAssessment"]["ruleTransitions"]
            or manifest["changeAssessment"]["findingDelta"]["introduced"]
        )

    def test_manifest_is_repeatable_for_same_inputs(self):
        baseline = self._good_scan()
        current = self._negative_scan()
        first = build_evidence_manifest(current, baseline)
        second = build_evidence_manifest(current, baseline)
        self.assertEqual(first, second)
        self.assertRegex(first["evidenceDigest"], r"^sha256:[0-9a-f]{64}$")

    def test_repository_mismatch_is_rejected(self):
        baseline = self._good_scan()
        current = copy.deepcopy(baseline)
        current["repository"] = {"name": "different/product"}
        current["revision"] = {"sha": CURRENT_REVISION}
        with self.assertRaises(ValueError):
            build_evidence_manifest(current, baseline)

    def test_markdown_preserves_non_oracle_boundary(self):
        manifest = build_evidence_manifest(self._good_scan(), None)
        rendered = render_evidence_markdown(manifest)
        self.assertIn("Evidence continuity is not authorization continuity", rendered)
        self.assertIn("does not determine whether legal", rendered)


if __name__ == "__main__":
    unittest.main()
