#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema.validators import validator_for

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "rules/catalog.yaml"
RESULT_SCHEMA = ROOT / "schemas/scan-result.schema.json"
PLANNING_CATALOG = ROOT / "planning/catalog.yaml"
PLANNING_SCHEMA = ROOT / "schemas/planning-report.schema.json"
PRODUCT_MANIFEST_SCHEMA = ROOT / "schemas/product-manifest.schema.json"
PRODUCT_ASSESSMENT_SCHEMA = ROOT / "schemas/product-assessment.schema.json"
PRODUCT_PLANNING_SCHEMA = ROOT / "schemas/product-planning-report.schema.json"
EVIDENCE_MANIFEST_SCHEMA = ROOT / "schemas/evidence-manifest.schema.json"
EXPECTED = ROOT / "fixtures/expected-results.yaml"


def fail(message: str) -> None:
    raise SystemExit(message)


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def validate_machine_readable_files() -> None:
    catalog = load_yaml(CATALOG)
    planning_catalog = load_yaml(PLANNING_CATALOG)
    expected = load_yaml(EXPECTED)
    result_schema = json.loads(RESULT_SCHEMA.read_text(encoding="utf-8"))
    planning_schema = json.loads(PLANNING_SCHEMA.read_text(encoding="utf-8"))
    product_manifest_schema = json.loads(PRODUCT_MANIFEST_SCHEMA.read_text(encoding="utf-8"))
    product_assessment_schema = json.loads(PRODUCT_ASSESSMENT_SCHEMA.read_text(encoding="utf-8"))
    product_planning_schema = json.loads(PRODUCT_PLANNING_SCHEMA.read_text(encoding="utf-8"))
    evidence_manifest_schema = json.loads(EVIDENCE_MANIFEST_SCHEMA.read_text(encoding="utf-8"))

    if catalog.get("catalogVersion") != "iaap-guard/v0.1.2":
        fail("unexpected rule catalog version")
    if catalog.get("scoringModelVersion") != "coverage/v1":
        fail("unexpected scoring model version")
    if planning_catalog.get("planningCatalogVersion") != "iaap-planning/v0.1.0":
        fail("unexpected planning catalog version")
    if planning_catalog.get("schemaVersion") != "planning-report/v1":
        fail("unexpected planning report schema version")

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

    planning_rules = planning_catalog.get("rules") or {}
    missing_plans = set(ids) - set(planning_rules)
    if missing_plans:
        fail(f"rules missing planning templates: {sorted(missing_plans)}")
    extra_plans = set(planning_rules) - set(ids)
    if extra_plans:
        fail(f"planning templates reference unknown rules: {sorted(extra_plans)}")

    for rule_id, plan in planning_rules.items():
        for required in ("epic", "outcome", "feature", "story", "acceptanceEvidence", "candidateTasks"):
            if not plan.get(required):
                fail(f"{rule_id}: planning field {required} is required")
        story = plan["story"]
        for required in ("actor", "want", "soThat"):
            if not story.get(required):
                fail(f"{rule_id}: story field {required} is required")

    dimensions = set(catalog.get("dimensions") or [])
    planning_dimensions = set((planning_catalog.get("dimensions") or {}).keys())
    if planning_dimensions != dimensions:
        fail("planning dimensions must exactly match the scoring dimensions")

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

    for schema in (
        result_schema,
        planning_schema,
        product_manifest_schema,
        product_assessment_schema,
        product_planning_schema,
        evidence_manifest_schema,
    ):
        validator_cls = validator_for(schema)
        validator_cls.check_schema(schema)

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

    required_planning_fields = {
        "schemaVersion",
        "planningCatalogVersion",
        "status",
        "source",
        "totals",
        "objectives",
        "boundary",
    }
    if set(planning_schema.get("required", [])) != required_planning_fields:
        fail("planning-report schema required fields diverged from the V1 contract")

    if product_manifest_schema.get("properties", {}).get("schemaVersion", {}).get("const") != "iaap-product/v1":
        fail("unexpected product manifest schema version")
    if product_assessment_schema.get("properties", {}).get("schemaVersion", {}).get("const") != "product-assessment/v1":
        fail("unexpected product assessment schema version")
    if product_planning_schema.get("properties", {}).get("schemaVersion", {}).get("const") != "product-planning-report/v1":
        fail("unexpected product planning schema version")
    if evidence_manifest_schema.get("properties", {}).get("schemaVersion", {}).get("const") != "evidence-manifest/v1":
        fail("unexpected evidence manifest schema version")
    if evidence_manifest_schema.get("properties", {}).get("evidenceModelVersion", {}).get("const") != "continuity/v1":
        fail("unexpected evidence continuity model version")

    print(
        f"specification validation passed: {len(rules)} rules, "
        f"{len(case_paths)} fixtures, {len(required_fail_fixtures)} critical FAIL rules, "
        f"{len(planning_rules)} planning templates, 3 product-scope schemas, 1 evidence-continuity schema"
    )


if __name__ == "__main__":
    validate_machine_readable_files()
