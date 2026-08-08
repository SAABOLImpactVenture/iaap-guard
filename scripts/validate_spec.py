#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema.validators import validator_for

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "rules/catalog.yaml"
RESULT_SCHEMA = ROOT / "schemas/scan-result.schema.json"
EXPECTED = ROOT / "fixtures/expected-results.yaml"


def fail(message: str) -> None:
    raise SystemExit(message)


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def validate_machine_readable_files() -> None:
    catalog = load_yaml(CATALOG)
    expected = load_yaml(EXPECTED)
    result_schema = json.loads(RESULT_SCHEMA.read_text(encoding="utf-8"))

    if catalog.get("catalogVersion") != "iaap-guard/v0.1.2":
        fail("unexpected rule catalog version")
    if catalog.get("scoringModelVersion") != "coverage/v1":
        fail("unexpected scoring model version")

    rules = catalog.get("rules", [])
    ids = [rule.get("id") for rule in rules]
    if not ids or len(ids) != len(set(ids)):
        fail("rule IDs must be present and unique")

    valid_results = {"PASS", "WARNING", "FAIL", "NOT_APPLICABLE"}
    for rule in rules:
        if rule.get("violationResult") not in {"WARNING", "FAIL"}:
            fail(f"{rule.get('id')}: invalid violationResult")
        if rule.get("experimental") and rule.get("scoring"):
            fail(f"{rule.get('id')}: experimental rules must be non-scoring in V0")
        if not rule.get("appliesTo"):
            fail(f"{rule.get('id')}: appliesTo is required")
        if not rule.get("evidenceRequirement"):
            fail(f"{rule.get('id')}: evidenceRequirement is required")
        if not rule.get("recommendation"):
            fail(f"{rule.get('id')}: recommendation is required")

    case_paths: set[str] = set()
    critical_fixture_rules: set[str] = set()
    for case in expected.get("cases", []):
        rel = case.get("path")
        if not rel or rel in case_paths:
            fail("fixture expected-results paths must be present and unique")
        case_paths.add(rel)
        fixture_path = ROOT / "fixtures" / rel
        if not fixture_path.exists():
            fail(f"expected fixture does not exist: {rel}")

        results = case.get("expected", {})
        for rule_id, result in results.items():
            if rule_id not in ids:
                fail(f"{rel}: unknown rule ID {rule_id}")
            if result not in valid_results:
                fail(f"{rel}: invalid expected result {result}")
            if rel.startswith("negative/") and result == "FAIL":
                critical_fixture_rules.add(rule_id)

    required_fail_fixtures = {
        rule["id"] for rule in rules if rule.get("violationResult") == "FAIL"
    }
    missing = required_fail_fixtures - critical_fixture_rules
    if missing:
        fail(f"FAIL rules missing negative fixtures: {sorted(missing)}")

    for path in (ROOT / "fixtures").rglob("*.yaml"):
        list(yaml.safe_load_all(path.read_text(encoding="utf-8")))
    for path in (ROOT / "fixtures").rglob("*.json"):
        json.loads(path.read_text(encoding="utf-8"))

    validator_cls = validator_for(result_schema)
    validator_cls.check_schema(result_schema)

    required_result_fields = {
        "schemaVersion",
        "ruleCatalogVersion",
        "scoringModelVersion",
        "repository",
        "revision",
        "detectedComponents",
        "findings",
        "ruleResults",
        "dimensionScores",
        "overallScore",
        "conclusion",
    }
    if set(result_schema.get("required", [])) != required_result_fields:
        fail("scan-result schema required fields diverged from the Phase 8 contract")

    print(
        f"specification validation passed: {len(rules)} rules, "
        f"{len(case_paths)} fixtures, {len(required_fail_fixtures)} critical FAIL rules"
    )


if __name__ == "__main__":
    validate_machine_readable_files()
