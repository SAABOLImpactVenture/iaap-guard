from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable

import yaml

from .model import Artifact, Violation


def load_catalog(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _walk(value: Any) -> Iterable[Any]:
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _dicts(artifact: Artifact) -> Iterable[dict[str, Any]]:
    for document in artifact.documents:
        for value in _walk(document):
            if isinstance(value, dict):
                yield value


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _line(artifact: Artifact, needle: str) -> int | None:
    target = needle.lower()
    for number, line in enumerate(artifact.text.splitlines(), start=1):
        if target in line.lower():
            return number
    return None


def _artifacts_with(artifacts: list[Artifact], *contexts: str) -> list[Artifact]:
    wanted = set(contexts)
    return [artifact for artifact in artifacts if wanted & set(artifact.contexts)]


def _property_names(artifact: Artifact) -> Iterable[str]:
    for item in _dicts(artifact):
        properties = item.get("properties")
        if isinstance(properties, dict):
            yield from (str(name) for name in properties)


def _required_names(artifact: Artifact) -> Iterable[str]:
    for item in _dicts(artifact):
        required = item.get("required")
        if isinstance(required, list):
            yield from (str(name) for name in required)


def _actions(artifact: Artifact) -> Iterable[str]:
    for item in _dicts(artifact):
        action = item.get("action")
        if isinstance(action, str):
            yield action


def _root_dicts(artifact: Artifact) -> Iterable[dict[str, Any]]:
    for document in artifact.documents:
        if isinstance(document, dict):
            yield document


def _find_bool(artifact: Artifact, key: str, desired: bool) -> bool:
    for item in _dicts(artifact):
        if item.get(key) is desired:
            return True
    return False


def _list_values(artifact: Artifact, key: str) -> set[str]:
    result: set[str] = set()
    for item in _dicts(artifact):
        value = item.get(key)
        if isinstance(value, list):
            result.update(str(entry) for entry in value)
    return result


def _schema_properties(document: dict[str, Any], role: str) -> tuple[dict[str, Any], set[str]] | None:
    if isinstance(document.get("component"), str):
        expected = "canonical-product-contract" if role == "canonical" else "storefront-order-contract"
        if document["component"] == expected:
            schema = document.get("schema")
            if isinstance(schema, dict) and isinstance(schema.get("properties"), dict):
                return schema["properties"], set(schema.get("required") or [])

    kind = str(document.get("kind", ""))
    if role == "canonical" and kind == "CompositeResourceDefinition":
        versions = ((document.get("spec") or {}).get("versions") or [])
        for version in versions:
            if not isinstance(version, dict):
                continue
            schema = (((version.get("schema") or {}).get("openAPIV3Schema") or {}).get("properties") or {}).get("spec")
            if isinstance(schema, dict) and isinstance(schema.get("properties"), dict):
                return schema["properties"], set(schema.get("required") or [])

    if role == "canonical" and kind == "InfrastructureProductSchema":
        spec = document.get("spec") or {}
        properties = spec.get("properties")
        if isinstance(properties, dict):
            return properties, set(spec.get("required") or [])

    if role == "storefront" and kind == "Template":
        spec = document.get("spec") or {}
        combined: dict[str, Any] = {}
        required: set[str] = set()
        for group in spec.get("parameters") or []:
            if not isinstance(group, dict):
                continue
            if isinstance(group.get("properties"), dict):
                combined.update(group["properties"])
            if isinstance(group.get("required"), list):
                required.update(str(value) for value in group["required"])
        if combined:
            return combined, required

    # A structured order JSON Schema may be used as an experience contract.
    if role == "storefront" and isinstance(document.get("properties"), dict):
        spec = document["properties"].get("spec")
        if isinstance(spec, dict) and isinstance(spec.get("properties"), dict):
            return spec["properties"], set(spec.get("required") or [])
    return None


def _contracts(artifacts: list[Artifact], role: str) -> list[tuple[Artifact, dict[str, Any], set[str]]]:
    context = "consumer-contract" if role == "canonical" else "experience"
    result: list[tuple[Artifact, dict[str, Any], set[str]]] = []
    for artifact in _artifacts_with(artifacts, context):
        for document in _root_dicts(artifact):
            extracted = _schema_properties(document, role)
            if extracted:
                result.append((artifact, extracted[0], extracted[1]))
    return result


def _compare_constraints(
    canonical: dict[str, Any], storefront: dict[str, Any]
) -> list[str]:
    problems: list[str] = []
    for field in sorted(set(canonical) & set(storefront)):
        product = canonical.get(field) if isinstance(canonical.get(field), dict) else {}
        consumer = storefront.get(field) if isinstance(storefront.get(field), dict) else {}
        product_enum = set(product.get("enum") or [])
        consumer_enum = set(consumer.get("enum") or [])
        if product_enum and consumer_enum and not consumer_enum <= product_enum:
            problems.append(f"{field}: consumer enum includes {sorted(consumer_enum - product_enum)!r}")
        product_min = product.get("minLength")
        consumer_min = consumer.get("minLength")
        if product_min is not None and (consumer_min is None or consumer_min < product_min):
            problems.append(f"{field}: consumer minLength {consumer_min!r} is broader than {product_min!r}")
        product_max = product.get("maxLength")
        consumer_max = consumer.get("maxLength")
        if product_max is not None and (consumer_max is None or consumer_max > product_max):
            problems.append(f"{field}: consumer maxLength {consumer_max!r} is broader than {product_max!r}")
        product_pattern = product.get("pattern")
        consumer_pattern = consumer.get("pattern")
        if product_pattern and consumer_pattern != product_pattern:
            problems.append(f"{field}: consumer pattern differs from canonical product pattern")
    return problems


def _validation_evidence(artifacts: list[Artifact]) -> bool:
    for artifact in artifacts:
        for document in _root_dicts(artifact):
            if str(document.get("kind", "")) == "ProductRepositoryEvidence":
                spec = document.get("spec") or {}
                paths = spec.get("deterministicValidationPaths")
                if isinstance(paths, list) and paths:
                    return True
                if spec.get("ciValidatesProductBoundary") is True:
                    return True
        if artifact.fixture:
            continue
        lower = artifact.relative_path.lower()
        name = Path(lower).name
        if lower.startswith("tests/") or "/tests/" in lower:
            if name.startswith("test_") or any(token in name for token in ("contract", "boundary", "policy", "authority", "evidence")):
                return True
        if lower.startswith("scripts/") and any(token in name for token in ("validate", "verify", "lint", "check")):
            return True
        if lower.startswith(".github/workflows/"):
            body = artifact.text.lower()
            if any(token in body for token in ("make validate", "make test", "pytest", "unittest", "scripts/validate", "scripts/verify")):
                return True
    return False


def _lifecycle_evidence(artifacts: list[Artifact]) -> bool:
    for artifact in artifacts:
        for item in _dicts(artifact):
            if "status" in item and isinstance(item.get("status"), (dict, list)):
                return True
            if any(key in item for key in ("statusEvidencePaths", "teardownEvidence", "reconciliationEvidence", "orphanCheck")):
                return True
        if artifact.fixture:
            continue
        lower = artifact.relative_path.lower()
        if any(token in lower for token in ("teardown", "uninstall", "cleanup", "orphan", "validate-runtime", "reconciliation", "render_evidence", "collect_evidence")):
            return True
    return False


def _rule_p001(artifacts: list[Artifact], rule: dict[str, Any]) -> tuple[str, list[Violation]]:
    relevant = _artifacts_with(artifacts, "consumer-contract", "experience")
    if not relevant:
        return "NOT_APPLICABLE", []
    prohibited = {_normalize(value) for value in rule.get("examples", {}).get("prohibitedInConsumerSurface", [])}
    prohibited.update({"providerconfigref", "workspace", "iampolicyjson"})
    violations: list[Violation] = []
    for artifact in relevant:
        for field in _property_names(artifact):
            if _normalize(field) in prohibited:
                violations.append(Violation(artifact, f"consumer-facing field {field!r} exposes implementation machinery", _line(artifact, field)))
    return (rule["violationResult"], violations) if violations else ("PASS", [])


def _rule_p002(artifacts: list[Artifact], rule: dict[str, Any]) -> tuple[str, list[Violation]]:
    relevant = _artifacts_with(artifacts, "consumer-contract", "experience")
    if not relevant:
        return "NOT_APPLICABLE", []
    lifecycle = {"deletionpolicy", "lifecyclepolicy", "managementpolicies", "orphanpolicy", "retentionpolicy"}
    violations: list[Violation] = []
    for artifact in relevant:
        for field in _property_names(artifact):
            if _normalize(field) in lifecycle:
                violations.append(Violation(artifact, f"consumer-facing field {field!r} makes platform lifecycle consumer-selectable", _line(artifact, field)))
    return (rule["violationResult"], violations) if violations else ("PASS", [])


def _rule_x001(artifacts: list[Artifact], rule: dict[str, Any]) -> tuple[str, list[Violation]]:
    relevant = _artifacts_with(artifacts, "experience")
    if not relevant:
        return "NOT_APPLICABLE", []
    direct = re.compile(r"(?:kubernetes|kubectl|terraform|tofu|tfe|aws|gcp|azure|cloud)[^\n:]*(?::|[-_]).*(?:apply|delete|create|provision|run)|(?:apply|delete|provision)[-_:]?(?:resource|infrastructure)", re.I)
    violations: list[Violation] = []
    for artifact in relevant:
        for action in _actions(artifact):
            if action == "publish:github:pull-request":
                continue
            if direct.search(action) or action.lower() in {"kubernetes:apply", "terraform:apply", "kubectl:apply"}:
                violations.append(Violation(artifact, f"experience action {action!r} directly executes infrastructure", _line(artifact, action), "experience"))
    return (rule["violationResult"], violations) if violations else ("PASS", [])


def _rule_a001(artifacts: list[Artifact], rule: dict[str, Any]) -> tuple[str, list[Violation]]:
    relevant = _artifacts_with(artifacts, "ai-authority")
    if not relevant:
        return "NOT_APPLICABLE", []
    dangerous = {"kubectl", "terraform", "tofu", "tfe-run", "cloud-admin", "kubernetes-admin", "read-secret", "apply-resource", "delete-resource", "credential-access"}
    violations: list[Violation] = []
    for artifact in relevant:
        reasons: list[str] = []
        for key in ("allowDirectApply", "allowCredentialAccess", "allowCloudAdmin", "allowKubernetesAdmin"):
            if _find_bool(artifact, key, True):
                reasons.append(f"{key}=true")
        granted = _list_values(artifact, "allowed") | _list_values(artifact, "allowedTools")
        unsafe = dangerous & granted
        if unsafe:
            reasons.append(f"granted dangerous tools {sorted(unsafe)!r}")
        if reasons:
            violations.append(Violation(artifact, "; ".join(reasons), _line(artifact, reasons[0].split("=")[0])))
    return (rule["violationResult"], violations) if violations else ("PASS", [])


def _rule_a002(artifacts: list[Artifact], rule: dict[str, Any]) -> tuple[str, list[Violation]]:
    relevant = _artifacts_with(artifacts, "ai-authority", "experience", "evidence")
    if not relevant:
        return "NOT_APPLICABLE", []
    violations: list[Violation] = []
    for artifact in relevant:
        bypass = (
            _find_bool(artifact, "allowSelfApproval", True)
            or _find_bool(artifact, "allowMergeOwnProposal", True)
            or _find_bool(artifact, "bypassHumanApproval", True)
        )
        proposal_without_approval = _find_bool(artifact, "proposalMode", True) and _find_bool(artifact, "requireHumanApproval", False)
        if bypass or proposal_without_approval:
            violations.append(Violation(artifact, "automation can bypass accountable human approval", _line(artifact, "allowSelfApproval") or _line(artifact, "requireHumanApproval")))
    return (rule["violationResult"], violations) if violations else ("PASS", [])


def _rule_c001(artifacts: list[Artifact], rule: dict[str, Any]) -> tuple[str, list[Violation]]:
    canonical = _contracts(artifacts, "canonical")
    storefront = _contracts(artifacts, "storefront")
    if not canonical or not storefront:
        return "NOT_APPLICABLE", []
    violations: list[Violation] = []
    for product_artifact, product, _ in canonical:
        for consumer_artifact, consumer, _ in storefront:
            problems = _compare_constraints(product, consumer)
            if problems:
                violations.append(Violation(consumer_artifact, "; ".join(problems), 1, "experience"))
    return (rule["violationResult"], violations) if violations else ("PASS", [])


def _rule_p003(artifacts: list[Artifact], rule: dict[str, Any]) -> tuple[str, list[Violation]]:
    implementations = [artifact for artifact in _artifacts_with(artifacts, "control-plane-implementation") if "bootstrap" not in artifact.contexts]
    if not implementations:
        return "NOT_APPLICABLE", []
    if _artifacts_with(artifacts, "consumer-contract"):
        return "PASS", []
    artifact = implementations[0]
    return rule["violationResult"], [Violation(artifact, "infrastructure implementation is present without a recognizable consumer product contract", 1)]


def _rule_p004(artifacts: list[Artifact], rule: dict[str, Any]) -> tuple[str, list[Violation]]:
    relevant = _artifacts_with(artifacts, "consumer-contract")
    if not relevant:
        return "NOT_APPLICABLE", []
    accountable = {"owner", "team", "ownerteam", "productowner", "platformowner"}
    for artifact in relevant:
        if any(_normalize(name) in accountable for name in _required_names(artifact)):
            return "PASS", []
    artifact = relevant[0]
    return rule["violationResult"], [Violation(artifact, "product contract does not require owner/team accountability metadata", 1)]


def _rule_g001(artifacts: list[Artifact], rule: dict[str, Any]) -> tuple[str, list[Violation]]:
    relevant = _artifacts_with(artifacts, "consumer-contract", "experience", "control-plane-implementation")
    if not relevant:
        return "NOT_APPLICABLE", []
    if _validation_evidence(artifacts):
        return "PASS", []
    artifact = relevant[0]
    return rule["violationResult"], [Violation(artifact, "no independently executable deterministic product-boundary validation was detected in analyzed scope", 1)]


def _rule_e001(artifacts: list[Artifact], rule: dict[str, Any]) -> tuple[str, list[Violation]]:
    relevant = _artifacts_with(artifacts, "consumer-contract", "control-plane-implementation", "evidence")
    if not relevant:
        return "NOT_APPLICABLE", []
    if _lifecycle_evidence(artifacts):
        return "PASS", []
    artifact = relevant[0]
    return rule["violationResult"], [Violation(artifact, "no machine-observable status, reconciliation, teardown, or lifecycle evidence path was detected", 1)]


def _rule_cx01(artifacts: list[Artifact], rule: dict[str, Any]) -> tuple[str, list[Violation]]:
    ownership: list[tuple[Artifact, dict[str, Any]]] = []
    for artifact in _artifacts_with(artifacts, "control-plane-implementation", "bootstrap"):
        for document in _root_dicts(artifact):
            if str(document.get("kind", "")) == "ReconciliationOwnership":
                ownership.append((artifact, document))
    if not ownership:
        return "NOT_APPLICABLE", []
    violations: list[Violation] = []
    for artifact, document in ownership:
        spec = document.get("spec") or {}
        reconcilers = spec.get("activeReconcilers") or []
        if isinstance(reconcilers, list) and len(reconcilers) > 1 and spec.get("handoffDeclared") is not True:
            violations.append(Violation(artifact, f"{len(reconcilers)} active reconcilers are declared for {spec.get('externalResource', 'one external resource')!r} without a handoff", _line(artifact, "activeReconcilers")))
    return (rule["violationResult"], violations) if violations else ("PASS", [])


EVALUATORS = {
    "IAP-P001": _rule_p001,
    "IAP-P002": _rule_p002,
    "IAP-X001": _rule_x001,
    "IAP-A001": _rule_a001,
    "IAP-A002": _rule_a002,
    "IAP-C001": _rule_c001,
    "IAP-P003": _rule_p003,
    "IAP-P004": _rule_p004,
    "IAP-G001": _rule_g001,
    "IAP-E001": _rule_e001,
    "IAP-CX01": _rule_cx01,
}


def evaluate_rules(
    artifacts: list[Artifact], catalog: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rule_results: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    for rule in catalog["rules"]:
        rule_id = rule["id"]
        evaluator = EVALUATORS.get(rule_id)
        if evaluator is None:
            result, violations = "NOT_APPLICABLE", []
        else:
            result, violations = evaluator(artifacts, rule)
        rule_results.append(
            {
                "ruleId": rule_id,
                "result": result,
                "dimension": rule["dimension"],
                "scoring": bool(rule.get("scoring")),
                "experimental": bool(rule.get("experimental")),
            }
        )
        for violation in violations:
            if result not in {"WARNING", "FAIL"}:
                continue
            context = violation.context or next(
                (value for value in rule.get("appliesTo", []) if value in violation.artifact.contexts),
                violation.artifact.contexts[0],
            )
            finding = {
                "ruleId": rule_id,
                "result": result,
                "dimension": rule["dimension"],
                "componentContext": context,
                "path": violation.artifact.relative_path,
                "evidence": violation.evidence,
                "recommendation": rule["recommendation"],
                "scoring": bool(rule.get("scoring")),
                "experimental": bool(rule.get("experimental")),
            }
            if violation.line is not None:
                finding["line"] = violation.line
            findings.append(finding)
    return rule_results, findings
