from __future__ import annotations

from copy import deepcopy
from typing import Any

RELATIONSHIP_RULE_IDS = {"IAP-C001"}
CONCLUSION_ORDER = {"success": 0, "neutral": 1, "failure": 2, "incomplete": 3}


def _source_repository(path: str) -> tuple[str, str]:
    parts = path.split("/")
    if len(parts) >= 4 and parts[0] == "members":
        repository = f"{parts[1]}/{parts[2]}"
        relative = "/".join(parts[3:]) or "unknown"
        return repository, relative
    return "@product", path


def _recalculate_overall(dimensions: list[dict[str, Any]]) -> int | None:
    values = [item["score"] for item in dimensions if item.get("score") is not None]
    return round(sum(values) / len(values)) if values else None


def apply_relationship_evidence(
    assessment: dict[str, Any],
    relationship_scan: dict[str, Any],
) -> dict[str, Any]:
    """Overlay controls whose current semantics genuinely require member coexistence.

    V1 deliberately limits this pass to IAP-C001: canonical product-contract and
    consumer/storefront constraint compatibility. Other controls remain owned by
    member repository scans until their cross-repository semantics are explicitly
    versioned rather than inferred or double-counted.
    """

    output = deepcopy(assessment)
    relationship_results = [
        item
        for item in relationship_scan.get("ruleResults", [])
        if item.get("ruleId") in RELATIONSHIP_RULE_IDS
        and item.get("result") != "NOT_APPLICABLE"
    ]
    if not relationship_results:
        return output

    by_dimension = {item["dimension"]: item for item in output.get("dimensionScores", [])}
    for result in relationship_results:
        if not result.get("scoring"):
            continue
        dimension = result["dimension"]
        record = by_dimension.get(dimension)
        if record is None:
            record = {"dimension": dimension, "passed": 0, "applicable": 0, "score": None}
            output["dimensionScores"].append(record)
            by_dimension[dimension] = record
        record["applicable"] += 1
        if result.get("result") == "PASS":
            record["passed"] += 1
        record["score"] = round((record["passed"] / record["applicable"]) * 100)

    relationship_findings = []
    for finding in relationship_scan.get("findings", []):
        if finding.get("ruleId") not in RELATIONSHIP_RULE_IDS:
            continue
        item = dict(finding)
        repository, relative = _source_repository(str(item.get("path") or "unknown"))
        item["repository"] = repository
        item["path"] = relative
        relationship_findings.append(item)
    output["findings"].extend(relationship_findings)
    output["overallScore"] = _recalculate_overall(output["dimensionScores"])

    if output["conclusion"] != "incomplete":
        relationship_conclusion = "success"
        if any(item.get("result") == "FAIL" for item in relationship_results):
            relationship_conclusion = "failure"
        elif any(item.get("result") == "WARNING" for item in relationship_results):
            relationship_conclusion = "neutral"
        output["conclusion"] = max(
            (output["conclusion"], relationship_conclusion),
            key=lambda value: CONCLUSION_ORDER.get(str(value), 3),
        )
    return output
