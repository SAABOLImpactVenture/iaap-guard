from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .loader import load_artifacts
from .model import CONTEXT_ORDER
from .rules import evaluate_rules, load_catalog
from .scoring import score_results

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG = ROOT / "rules" / "catalog.yaml"


def scan_path(
    target: str | Path,
    *,
    repository: str | None = None,
    revision: str = "0" * 40,
    ref: str | None = None,
    catalog_path: str | Path | None = None,
) -> dict[str, Any]:
    target_path = Path(target).resolve()
    if not target_path.exists():
        raise FileNotFoundError(target_path)
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("revision must be a 40-character lowercase hexadecimal SHA")

    catalog = load_catalog(Path(catalog_path) if catalog_path else DEFAULT_CATALOG)
    artifacts = load_artifacts(target_path)
    rule_results, findings = evaluate_rules(artifacts, catalog)
    dimension_scores, overall, conclusion = score_results(rule_results, catalog["dimensions"])

    present = {context for artifact in artifacts for context in artifact.contexts}
    detected = [context for context in CONTEXT_ORDER if context in present]

    revision_record: dict[str, str] = {"sha": revision}
    if ref is not None:
        revision_record["ref"] = ref

    if repository is None:
        repository = target_path.name if target_path.is_dir() else target_path.parent.name

    return {
        "schemaVersion": "scan-result/v1",
        "ruleCatalogVersion": catalog["catalogVersion"],
        "scoringModelVersion": catalog["scoringModelVersion"],
        "repository": {"name": repository},
        "revision": revision_record,
        "detectedComponents": detected,
        "findings": findings,
        "ruleResults": rule_results,
        "dimensionScores": dimension_scores,
        "overallScore": overall,
        "conclusion": conclusion,
    }
