from __future__ import annotations

from typing import Any


def score_results(
    rule_results: list[dict[str, Any]], dimensions: list[str]
) -> tuple[list[dict[str, Any]], int | None, str]:
    dimension_scores: list[dict[str, Any]] = []
    for dimension in dimensions:
        applicable = [
            result
            for result in rule_results
            if result["dimension"] == dimension
            and result["scoring"]
            and result["result"] != "NOT_APPLICABLE"
        ]
        passed = sum(1 for result in applicable if result["result"] == "PASS")
        score = round((passed / len(applicable)) * 100) if applicable else None
        dimension_scores.append(
            {
                "dimension": dimension,
                "passed": passed,
                "applicable": len(applicable),
                "score": score,
            }
        )

    scored_dimensions = [item["score"] for item in dimension_scores if item["score"] is not None]
    overall = round(sum(scored_dimensions) / len(scored_dimensions)) if scored_dimensions else None

    scoring_results = [result for result in rule_results if result["scoring"]]
    if any(result["result"] == "FAIL" for result in scoring_results):
        conclusion = "failure"
    elif any(result["result"] == "WARNING" for result in scoring_results):
        conclusion = "neutral"
    else:
        conclusion = "success"

    return dimension_scores, overall, conclusion
