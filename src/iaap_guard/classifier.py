from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from .model import CONTEXT_ORDER


def _walk(value: Any) -> Iterable[Any]:
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _dicts(documents: tuple[Any, ...]) -> Iterable[dict[str, Any]]:
    for document in documents:
        for value in _walk(document):
            if isinstance(value, dict):
                yield value


def _ordered(contexts: set[str]) -> tuple[str, ...]:
    if not contexts:
        return ("unknown",)
    return tuple(context for context in CONTEXT_ORDER if context in contexts)


def classify(
    path: Path,
    relative_path: str,
    documents: tuple[Any, ...],
    text: str,
    fixture: dict[str, Any] | None = None,
) -> tuple[str, ...]:
    """Classify an artifact before rule evaluation.

    Fixture metadata is an explicit single-fixture test harness override.
    During a normal repository scan, files beneath fixtures/ remain test data
    regardless of the unsafe architecture they intentionally contain.
    """
    fixture = fixture or {}
    explicit: set[str] = set()
    if isinstance(fixture.get("context"), str):
        explicit.add(fixture["context"])
    if isinstance(fixture.get("contexts"), list):
        explicit.update(str(item) for item in fixture["contexts"])
    if explicit:
        return _ordered(explicit)

    lower_path = relative_path.lower()
    if lower_path.startswith("fixtures/"):
        return ("documentation-fixture",)

    contexts: set[str] = set()
    dicts = list(_dicts(documents))
    kinds = {str(item.get("kind", "")).lower() for item in dicts if item.get("kind")}
    api_versions = {str(item.get("apiVersion", "")).lower() for item in dicts if item.get("apiVersion")}

    if lower_path.endswith(".md") or lower_path.startswith("docs/"):
        contexts.add("documentation-fixture")

    if "template" in kinds and any("scaffolder.backstage.io" in value for value in api_versions):
        contexts.add("experience")

    if kinds & {
        "compositeresourcedefinition",
        "infrastructureproductschema",
        "productcontract",
    }:
        contexts.add("consumer-contract")

    if any(
        isinstance(item.get("component"), str)
        and item["component"] == "canonical-product-contract"
        for item in dicts
    ):
        contexts.add("consumer-contract")
    if any(
        isinstance(item.get("component"), str)
        and item["component"] == "storefront-order-contract"
        for item in dicts
    ):
        contexts.add("experience")

    if kinds & {"composition", "providerconfig", "provider", "implementationinventory", "reconciliationownership"}:
        contexts.add("control-plane-implementation")
    if path.suffix.lower() in {".tf", ".tofu", ".hcl"}:
        contexts.add("control-plane-implementation")

    if kinds & {"productrepositoryevidence", "evidencerecord", "evidencebundle"}:
        contexts.add("evidence")

    if lower_path.startswith("tests/") or "/tests/" in lower_path:
        contexts.add("evidence")
    if lower_path.startswith(".github/workflows/"):
        contexts.add("evidence")
    if lower_path.startswith("scripts/") and any(token in lower_path for token in ("validate", "verify", "evidence", "score")):
        contexts.add("evidence")

    ai_keys = {
        "allowDirectApply",
        "allowCredentialAccess",
        "requireHumanApproval",
        "allowSelfApproval",
        "allowMergeOwnProposal",
        "allowed",
        "denied",
        "allowedTools",
    }
    if any(ai_keys & set(item) for item in dicts):
        contexts.add("ai-authority")

    lower_text = text.lower()
    if (
        "minimal-trusted-bootstrap" in lower_text
        or "consumerproductsownedhere" in lower_text
        or "bootstrap" in lower_path
        or "seed" in lower_path
    ):
        contexts.add("bootstrap")

    # JSON Schema/OpenAPI product/order contracts are recognized by path only
    # when their purpose is explicit. Generic schemas remain unknown/evidence.
    if not contexts and path.suffix.lower() == ".json" and "schema" in lower_path:
        if any(token in lower_path for token in ("product", "order", "request", "contract")):
            contexts.add("consumer-contract")

    return _ordered(contexts)
