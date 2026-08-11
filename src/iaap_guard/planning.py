from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PLANNING_CATALOG = ROOT / "planning" / "catalog.yaml"


def load_planning_catalog(path: str | Path | None = None) -> dict[str, Any]:
    catalog_path = Path(path) if path is not None else DEFAULT_PLANNING_CATALOG
    return yaml.safe_load(catalog_path.read_text(encoding="utf-8"))


def _dimension_score_map(result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        item["dimension"]: item
        for item in result.get("dimensionScores", [])
        if isinstance(item, dict) and isinstance(item.get("dimension"), str)
    }


def _finding_reference(finding: dict[str, Any]) -> dict[str, Any]:
    reference = {
        "ruleId": finding.get("ruleId"),
        "result": finding.get("result"),
        "path": finding.get("path"),
        "evidence": finding.get("evidence"),
        "recommendation": finding.get("recommendation"),
        "experimental": bool(finding.get("experimental")),
    }
    if finding.get("line") is not None:
        reference["line"] = finding["line"]
    return reference


def _fallback_rule_plan(rule_id: str, findings: list[dict[str, Any]]) -> dict[str, Any]:
    recommendation = next(
        (str(item.get("recommendation")) for item in findings if item.get("recommendation")),
        "Resolve the deterministic architecture finding and capture passing evidence.",
    )
    return {
        "epic": f"Resolve {rule_id} architecture finding",
        "outcome": recommendation,
        "feature": f"{rule_id} remediation",
        "story": {
            "actor": "platform team",
            "want": "resolve the deterministic Infrastructure-as-a-Product finding",
            "soThat": "the product can demonstrate the intended architecture control",
        },
        "acceptanceEvidence": ["The affected Guard rule passes with reproducible evidence."],
        "candidateTasks": [recommendation, "Capture the resulting passing Guard evidence."],
    }


def _story_statement(story: dict[str, Any]) -> str:
    return (
        f"As a {story['actor']}, I want to {story['want']}, "
        f"so that {story['soThat']}."
    )


def build_planning_report(
    result: dict[str, Any],
    *,
    catalog_path: str | Path | None = None,
) -> dict[str, Any]:
    """Convert a deterministic scan-result/v1 document into planning-report/v1.

    The report is intentionally advisory. It creates evidence-traceable OKRs and
    candidate backlog detail, but it does not assign people, sequence sprints,
    create issues, or authorize implementation.
    """

    catalog = load_planning_catalog(catalog_path)
    findings = [item for item in result.get("findings", []) if isinstance(item, dict)]
    score_by_dimension = _dimension_score_map(result)

    findings_by_dimension: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for finding in findings:
        dimension = str(finding.get("dimension") or "Unclassified")
        rule_id = str(finding.get("ruleId") or "UNMAPPED")
        findings_by_dimension.setdefault(dimension, {}).setdefault(rule_id, []).append(finding)

    dimension_order = [
        item["dimension"]
        for item in result.get("dimensionScores", [])
        if isinstance(item, dict) and isinstance(item.get("dimension"), str)
    ]
    for dimension in findings_by_dimension:
        if dimension not in dimension_order:
            dimension_order.append(dimension)

    objectives: list[dict[str, Any]] = []
    totals = {
        "objectives": 0,
        "keyResults": 0,
        "epics": 0,
        "features": 0,
        "userStories": 0,
        "candidateTasks": 0,
    }

    for dimension in dimension_order:
        grouped_rules = findings_by_dimension.get(dimension)
        if not grouped_rules:
            continue

        objective_id = f"O{len(objectives) + 1}"
        dimension_plan = (catalog.get("dimensions") or {}).get(dimension) or {}
        objective_title = dimension_plan.get("objective") or f"Improve {dimension} architecture evidence."
        score_record = score_by_dimension.get(dimension) or {}
        baseline_score = score_record.get("score")
        total_findings = sum(len(items) for items in grouped_rules.values())
        fail_count = sum(
            1
            for items in grouped_rules.values()
            for item in items
            if item.get("result") == "FAIL"
        )

        key_results: list[dict[str, Any]] = []
        if baseline_score is not None:
            key_results.append(
                {
                    "id": f"{objective_id}-KR1",
                    "statement": f"Raise {dimension} evidence coverage from {baseline_score} to 100.",
                    "metric": "dimensionCoverage",
                    "baseline": baseline_score,
                    "target": 100,
                }
            )
        key_results.append(
            {
                "id": f"{objective_id}-KR{len(key_results) + 1}",
                "statement": f"Reduce unresolved {dimension} Guard findings from {total_findings} to 0.",
                "metric": "unresolvedGuardFindings",
                "baseline": total_findings,
                "target": 0,
            }
        )
        if fail_count:
            key_results.append(
                {
                    "id": f"{objective_id}-KR{len(key_results) + 1}",
                    "statement": f"Reduce blocking {dimension} FAIL findings from {fail_count} to 0.",
                    "metric": "blockingGuardFindings",
                    "baseline": fail_count,
                    "target": 0,
                }
            )

        epics: list[dict[str, Any]] = []
        for rule_id, rule_findings in grouped_rules.items():
            rule_plan = (catalog.get("rules") or {}).get(rule_id) or _fallback_rule_plan(rule_id, rule_findings)
            epic_id = f"{objective_id}-E{len(epics) + 1}"
            mapped_kr_ids = [item["id"] for item in key_results]
            story = rule_plan["story"]
            candidate_tasks = [
                {"id": f"{epic_id}-T{index}", "title": task, "candidate": True}
                for index, task in enumerate(rule_plan.get("candidateTasks") or [], start=1)
            ]
            feature = {
                "id": f"{epic_id}-F1",
                "title": rule_plan["feature"],
                "userStories": [
                    {
                        "id": f"{epic_id}-US1",
                        "statement": _story_statement(story),
                        "candidate": True,
                        "acceptanceEvidence": list(rule_plan.get("acceptanceEvidence") or []),
                        "candidateTasks": candidate_tasks,
                    }
                ],
            }
            epics.append(
                {
                    "id": epic_id,
                    "ruleId": rule_id,
                    "title": rule_plan["epic"],
                    "outcome": rule_plan["outcome"],
                    "keyResultIds": mapped_kr_ids,
                    "findingCount": len(rule_findings),
                    "experimental": all(bool(item.get("experimental")) for item in rule_findings),
                    "evidence": [_finding_reference(item) for item in rule_findings],
                    "features": [feature],
                }
            )
            totals["epics"] += 1
            totals["features"] += 1
            totals["userStories"] += 1
            totals["candidateTasks"] += len(candidate_tasks)

        objectives.append(
            {
                "id": objective_id,
                "dimension": dimension,
                "title": objective_title,
                "baselineScore": baseline_score,
                "targetScore": 100 if baseline_score is not None else None,
                "keyResults": key_results,
                "epics": epics,
            }
        )
        totals["objectives"] += 1
        totals["keyResults"] += len(key_results)

    source = {
        "scanSchemaVersion": result.get("schemaVersion"),
        "ruleCatalogVersion": result.get("ruleCatalogVersion"),
        "scoringModelVersion": result.get("scoringModelVersion"),
        "repository": result.get("repository"),
        "revision": result.get("revision"),
        "conclusion": result.get("conclusion"),
        "overallScore": result.get("overallScore"),
        "findingCount": len(findings),
    }

    return {
        "schemaVersion": catalog.get("schemaVersion", "planning-report/v1"),
        "planningCatalogVersion": catalog["planningCatalogVersion"],
        "status": "improvement-required" if findings else "no-current-findings",
        "source": source,
        "totals": totals,
        "objectives": objectives,
        "boundary": {
            "advisory": True,
            "candidateBacklogOnly": True,
            "doesNotExecuteWork": True,
            "doesNotManageSprints": True,
        },
    }


def render_planning_markdown(report: dict[str, Any], *, include_header: bool = True) -> str:
    source = report["source"]
    repository = (source.get("repository") or {}).get("name", "unknown")
    revision = (source.get("revision") or {}).get("sha", "unknown")
    score = source.get("overallScore")
    score_text = "N/A" if score is None else str(score)

    lines: list[str] = []
    if include_header:
        lines.extend(
            [
                "# IaaP Guard Improvement Plan",
                "",
                f"Repository: `{repository}`  ",
                f"Revision: `{revision}`  ",
                f"Architecture score: **{score_text}**  ",
                f"Planning catalog: `{report['planningCatalogVersion']}`",
                "",
                "> Candidate stories and tasks are planning assistance, not execution commitments, assignments, or sprint state.",
                "",
            ]
        )

    if not report.get("objectives"):
        lines.append("No current Guard findings require an improvement plan.")
        return "\n".join(lines).rstrip() + "\n"

    totals = report["totals"]
    lines.extend(
        [
            f"Plan scope: **{totals['objectives']} objectives · {totals['keyResults']} key results · {totals['epics']} epics · {totals['features']} features · {totals['userStories']} candidate stories · {totals['candidateTasks']} candidate tasks**",
            "",
        ]
    )

    for objective in report["objectives"]:
        lines.extend(
            [
                f"## {objective['id']} — {objective['title']}",
                "",
                f"Dimension: **{objective['dimension']}**  ",
                f"Baseline score: **{objective['baselineScore'] if objective['baselineScore'] is not None else 'N/A'}**",
                "",
                "### Key Results",
                "",
            ]
        )
        for kr in objective["keyResults"]:
            lines.append(f"- **{kr['id']}** — {kr['statement']}")
        lines.append("")

        for epic in objective["epics"]:
            experimental = " · experimental" if epic.get("experimental") else ""
            lines.extend(
                [
                    f"### {epic['id']} — {epic['title']}{experimental}",
                    "",
                    f"Maps to: {', '.join(f'`{item}`' for item in epic['keyResultIds'])}  ",
                    f"Guard rule: `{epic['ruleId']}` · findings: **{epic['findingCount']}**  ",
                    f"Outcome: {epic['outcome']}",
                    "",
                ]
            )
            for feature in epic["features"]:
                lines.extend([f"#### Feature {feature['id']} — {feature['title']}", ""])
                for story in feature["userStories"]:
                    lines.extend(
                        [
                            f"**Candidate User Story {story['id']}**  ",
                            story["statement"],
                            "",
                            "Acceptance evidence:",
                        ]
                    )
                    for evidence in story["acceptanceEvidence"]:
                        lines.append(f"- {evidence}")
                    lines.extend(["", "Candidate tasks:"])
                    for task in story["candidateTasks"]:
                        lines.append(f"- [ ] **{task['id']}** — {task['title']}")
                    lines.append("")

            lines.append("Traceability:")
            for evidence in epic["evidence"]:
                location = str(evidence.get("path") or "unknown")
                if evidence.get("line") is not None:
                    location += f":{evidence['line']}"
                lines.append(
                    f"- `{location}` — **{evidence.get('result')} {evidence.get('ruleId')}** — {evidence.get('evidence')}"
                )
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"
