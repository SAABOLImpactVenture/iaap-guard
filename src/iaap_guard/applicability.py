from __future__ import annotations

from typing import Any

from .model import Artifact


def enforce_catalog_applicability(
    rule_results: list[dict[str, Any]],
    findings: list[dict[str, Any]],
    artifacts: list[Artifact],
    catalog: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Apply catalog-declared context applicability before scoring.

    Rule evaluators remain responsible for domain-specific evidence. This layer
    prevents a rule from becoming applicable merely because a generic evidence
    artifact exists when none of the rule's declared product contexts are
    present. Paired-context requirements are also enforced here.
    """
    present_contexts = {
        context
        for artifact in artifacts
        for context in artifact.contexts
    }
    rules = {rule["id"]: rule for rule in catalog.get("rules", [])}
    suppressed: set[str] = set()

    for result in rule_results:
        rule = rules.get(result.get("ruleId"))
        if not rule:
            continue

        applies_to = set(rule.get("appliesTo") or [])
        paired = set(rule.get("requiresPairedContexts") or [])

        applicable = True
        if applies_to and not (applies_to & present_contexts):
            applicable = False
        if paired and not paired <= present_contexts:
            applicable = False

        if not applicable:
            result["result"] = "NOT_APPLICABLE"
            suppressed.add(result["ruleId"])

    if suppressed:
        findings = [
            finding for finding in findings
            if finding.get("ruleId") not in suppressed
        ]

    return rule_results, findings
