from __future__ import annotations

import hashlib
import json
from typing import Any

EVIDENCE_MODEL_VERSION = "continuity/v1"


def _canonical_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _validate_scan_result(result: dict[str, Any], *, label: str) -> None:
    if result.get("schemaVersion") != "scan-result/v1":
        raise ValueError(f"{label} must be a scan-result/v1 document")
    repository = result.get("repository") or {}
    revision = result.get("revision") or {}
    if not isinstance(repository.get("name"), str) or not repository["name"]:
        raise ValueError(f"{label} repository name is required")
    if not isinstance(revision.get("sha"), str) or len(revision["sha"]) != 40:
        raise ValueError(f"{label} revision SHA is required")


def _rule_state(result: dict[str, Any]) -> dict[str, str]:
    state: dict[str, str] = {}
    for item in result.get("ruleResults", []):
        rule_id = item.get("ruleId")
        rule_result = item.get("result")
        if isinstance(rule_id, str) and isinstance(rule_result, str):
            state[rule_id] = rule_result
    return state


def _rule_transitions(current: dict[str, Any], baseline: dict[str, Any]) -> list[dict[str, Any]]:
    current_state = _rule_state(current)
    baseline_state = _rule_state(baseline)
    transitions: list[dict[str, Any]] = []
    for rule_id in sorted(set(current_state) | set(baseline_state)):
        before = baseline_state.get(rule_id)
        after = current_state.get(rule_id)
        if before != after:
            transitions.append({"ruleId": rule_id, "from": before, "to": after})
    return transitions


def _finding_record(finding: dict[str, Any]) -> dict[str, Any]:
    record: dict[str, Any] = {
        "ruleId": str(finding.get("ruleId", "unknown")),
        "result": str(finding.get("result", "WARNING")),
        "path": str(finding.get("path", "unknown")),
        "evidence": str(finding.get("evidence", "")),
    }
    line = finding.get("line")
    if isinstance(line, int):
        record["line"] = line
    return record


def _finding_key(record: dict[str, Any]) -> tuple[Any, ...]:
    return (
        record.get("ruleId"),
        record.get("result"),
        record.get("path"),
        record.get("line"),
        record.get("evidence"),
    )


def _finding_delta(current: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    current_records = [_finding_record(item) for item in current.get("findings", [])]
    baseline_records = [_finding_record(item) for item in baseline.get("findings", [])]
    current_map = {_finding_key(item): item for item in current_records}
    baseline_map = {_finding_key(item): item for item in baseline_records}
    introduced_keys = sorted(set(current_map) - set(baseline_map), key=str)
    resolved_keys = sorted(set(baseline_map) - set(current_map), key=str)
    unchanged = len(set(current_map) & set(baseline_map))
    return {
        "introduced": [current_map[key] for key in introduced_keys],
        "resolved": [baseline_map[key] for key in resolved_keys],
        "unchanged": unchanged,
    }


def build_evidence_manifest(
    current: dict[str, Any],
    baseline: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build deterministic, tamper-evident evidence about Guard state continuity.

    The manifest compares IaaP Guard evidence. It deliberately does not determine
    legal, institutional, deployment, or exception authority.
    """

    _validate_scan_result(current, label="current")
    if baseline is not None:
        _validate_scan_result(baseline, label="baseline")
        if baseline["repository"]["name"] != current["repository"]["name"]:
            raise ValueError("baseline and current scan results must describe the same repository")

    current_digest = _canonical_digest(current)
    baseline_digest = _canonical_digest(baseline) if baseline is not None else None

    if baseline is None:
        transitions: list[dict[str, Any]] = []
        delta = {"introduced": [], "resolved": [], "unchanged": 0}
        catalog_changed = False
        scoring_changed = False
        source_state_changed = False
        evidence_changed = False
        materiality = "unknown_without_baseline"
        continuity_status = "not_established"
        continuity_reasons = ["baseline_not_supplied"]
    else:
        transitions = _rule_transitions(current, baseline)
        delta = _finding_delta(current, baseline)
        catalog_changed = current.get("ruleCatalogVersion") != baseline.get("ruleCatalogVersion")
        scoring_changed = current.get("scoringModelVersion") != baseline.get("scoringModelVersion")
        source_state_changed = current["revision"]["sha"] != baseline["revision"]["sha"]
        evidence_changed = current_digest != baseline_digest
        guard_material_change = bool(
            catalog_changed
            or scoring_changed
            or transitions
            or delta["introduced"]
            or delta["resolved"]
        )
        materiality = "guard_material_change_detected" if guard_material_change else "no_guard_material_change_detected"

        continuity_reasons: list[str] = []
        if catalog_changed:
            continuity_reasons.append("rule_catalog_changed")
        if scoring_changed:
            continuity_reasons.append("scoring_model_changed")
        if transitions:
            continuity_reasons.append("rule_state_changed")
        if delta["introduced"] or delta["resolved"]:
            continuity_reasons.append("finding_evidence_changed")

        if continuity_reasons:
            continuity_status = "review_required"
        else:
            continuity_status = "supported"
            continuity_reasons.append(
                "identical_scan_evidence" if not evidence_changed else "current_state_revalidated_without_guard_material_change"
            )

    if baseline is None:
        disposition_status = "baseline_required"
        disposition_statement = (
            "This manifest establishes an evidence anchor only. A prior Guard result is required to assess continuity."
        )
    elif continuity_status == "review_required" or current.get("conclusion") in {"neutral", "failure"}:
        disposition_status = "human_review_required"
        disposition_statement = (
            "Guard evidence changed or the current scan contains a non-success conclusion. Accountable human review is required."
        )
    else:
        disposition_status = "no_additional_guard_review"
        disposition_statement = (
            "Within IaaP Guard's deterministic scope, current evidence supports continuity with the supplied baseline. "
            "This is not an authorization determination."
        )

    manifest: dict[str, Any] = {
        "schemaVersion": "evidence-manifest/v1",
        "evidenceModelVersion": EVIDENCE_MODEL_VERSION,
        "repository": {"name": current["repository"]["name"]},
        "currentRevision": current["revision"],
        "baselineRevision": baseline["revision"] if baseline is not None else None,
        "evidenceDigests": {
            "currentScan": current_digest,
            "baselineScan": baseline_digest,
        },
        "governanceState": {
            "currentRuleCatalogVersion": current.get("ruleCatalogVersion"),
            "baselineRuleCatalogVersion": baseline.get("ruleCatalogVersion") if baseline is not None else None,
            "currentScoringModelVersion": current.get("scoringModelVersion"),
            "baselineScoringModelVersion": baseline.get("scoringModelVersion") if baseline is not None else None,
            "currentConclusion": current.get("conclusion"),
            "baselineConclusion": baseline.get("conclusion") if baseline is not None else None,
        },
        "changeAssessment": {
            "sourceStateChanged": source_state_changed,
            "evidenceChanged": evidence_changed,
            "ruleCatalogChanged": catalog_changed,
            "scoringModelChanged": scoring_changed,
            "ruleStateChanged": bool(transitions),
            "findingEvidenceChanged": bool(delta["introduced"] or delta["resolved"]),
            "materiality": materiality,
            "ruleTransitions": transitions,
            "findingDelta": delta,
        },
        "evidenceContinuity": {
            "status": continuity_status,
            "reasons": continuity_reasons,
        },
        "authorityEvidence": {
            "status": "not_determined",
            "statement": (
                "IaaP Guard records and compares technical governance evidence. It does not determine whether legal, "
                "institutional, deployment, exception, or disposition authority exists or remains valid."
            ),
        },
        "disposition": {
            "status": disposition_status,
            "statement": disposition_statement,
        },
        "boundary": {
            "authorizationDetermination": False,
            "statement": (
                "Evidence continuity is not authorization continuity. Accountable humans and governing systems retain authority."
            ),
        },
    }
    manifest["evidenceDigest"] = _canonical_digest(manifest)
    return manifest


def render_evidence_markdown(manifest: dict[str, Any]) -> str:
    continuity = manifest["evidenceContinuity"]
    change = manifest["changeAssessment"]
    lines = [
        "# IaaP Guard Evidence Continuity",
        "",
        f"- Repository: `{manifest['repository']['name']}`",
        f"- Current revision: `{manifest['currentRevision']['sha']}`",
        f"- Baseline revision: `{manifest['baselineRevision']['sha'] if manifest['baselineRevision'] else 'not supplied'}`",
        f"- Continuity: **{continuity['status'].upper()}**",
        f"- Guard materiality: **{change['materiality']}**",
        f"- Disposition: **{manifest['disposition']['status']}**",
        f"- Evidence digest: `{manifest['evidenceDigest']}`",
        "",
        "## Continuity reasons",
        "",
    ]
    for reason in continuity["reasons"]:
        lines.append(f"- `{reason}`")

    transitions = change["ruleTransitions"]
    lines.extend(["", "## Rule-state transitions", ""])
    if transitions:
        for item in transitions:
            lines.append(f"- `{item['ruleId']}`: `{item['from']}` → `{item['to']}`")
    else:
        lines.append("- None detected.")

    delta = change["findingDelta"]
    lines.extend(["", "## Finding-evidence delta", ""])
    lines.append(f"- Introduced: {len(delta['introduced'])}")
    lines.append(f"- Resolved: {len(delta['resolved'])}")
    lines.append(f"- Unchanged: {delta['unchanged']}")

    lines.extend(
        [
            "",
            "## Product boundary",
            "",
            manifest["boundary"]["statement"],
            "",
            manifest["authorityEvidence"]["statement"],
            "",
        ]
    )
    return "\n".join(lines)
