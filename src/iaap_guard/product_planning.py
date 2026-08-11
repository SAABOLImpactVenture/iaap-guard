from __future__ import annotations

from typing import Any

from .planning import build_planning_report


def _planning_findings(assessment: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for item in assessment.get("findings") or []:
        finding = dict(item)
        repository = str(finding.get("repository") or "unknown")
        path = str(finding.get("path") or "unknown")
        finding["path"] = f"{repository}:{path}"
        findings.append(finding)
    return findings


def build_product_planning_report(assessment: dict[str, Any]) -> dict[str, Any]:
    """Create a product-scoped improvement plan from aggregated member evidence.

    The existing deterministic planning engine remains the source of Objective,
    KR, Epic, Feature, Story, and Task semantics. This adapter changes only the
    source scope from one repository to one registered product.
    """

    synthetic = {
        "schemaVersion": "scan-result/v1",
        "ruleCatalogVersion": assessment.get("ruleCatalogVersion"),
        "scoringModelVersion": assessment.get("scoringModelVersion"),
        "repository": {"name": f"product:{assessment['product']['id']}"},
        "revision": {"sha": assessment["evidenceRevision"][:40]},
        "detectedComponents": [],
        "findings": _planning_findings(assessment),
        "ruleResults": [],
        "dimensionScores": assessment.get("dimensionScores") or [],
        "overallScore": assessment.get("overallScore"),
        "conclusion": assessment.get("conclusion"),
    }
    base = build_planning_report(synthetic)
    return {
        "schemaVersion": "product-planning-report/v1",
        "planningCatalogVersion": base["planningCatalogVersion"],
        "status": base["status"],
        "source": {
            "product": assessment["product"],
            "evidenceRevision": assessment["evidenceRevision"],
            "productConclusion": assessment["conclusion"],
            "overallScore": assessment.get("overallScore"),
            "minimumMemberScore": assessment.get("minimumMemberScore"),
            "registeredRepositories": assessment["completeness"]["registered"],
            "presentRepositories": assessment["completeness"]["present"],
        },
        "totals": base["totals"],
        "objectives": base["objectives"],
        "boundary": {
            "advisory": True,
            "candidateBacklogOnly": True,
            "doesNotExecuteWork": True,
            "doesNotManageSprints": True,
            "doesNotExpandGitHubAppPermissions": True,
        },
    }


def render_product_planning_markdown(report: dict[str, Any]) -> str:
    source = report["source"]
    product = source["product"]
    lines = [
        f"# IaaP Guard Product Improvement Plan — {product['name']}",
        "",
        f"Product ID: `{product['id']}`  ",
        f"Conclusion: **{str(source['productConclusion']).upper()}**  ",
        f"Product evidence score: **{source['overallScore'] if source['overallScore'] is not None else 'N/A'}**  ",
        f"Weakest member score: **{source['minimumMemberScore'] if source['minimumMemberScore'] is not None else 'N/A'}**  ",
        f"Evidence coverage: **{source['presentRepositories']}/{source['registeredRepositories']} repositories**  ",
        f"Evidence revision: `{source['evidenceRevision']}`",
        "",
        "> Candidate stories and tasks are planning assistance. Product-level planning does not assign work, manage sprints, fetch related repositories, or expand GitHub App authority.",
        "",
    ]

    if not report.get("objectives"):
        lines.append("No current product findings require an improvement plan.")
        return "\n".join(lines) + "\n"

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
            lines.extend(
                [
                    f"### {epic['id']} — {epic['title']}",
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
                    lines.extend([f"**Candidate User Story {story['id']}**  ", story["statement"], "", "Acceptance evidence:"])
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
