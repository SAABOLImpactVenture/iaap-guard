# ADR 0004 — Lifecycle evidence requires control-plane implementation

**Status:** Accepted

## Context

Phase 9 dogfood against the Backstage storefront and Composite AI repositories produced the same `IAP-E001` warning. Both repositories participate in the infrastructure product architecture and contain structured consumer/AI contracts, but neither owns infrastructure reconciliation or managed-resource lifecycle.

Requiring reconciliation, teardown, or lifecycle evidence from those repositories creates a false obligation and penalizes separation of concerns.

## Decision

`IAP-E001` is applicable only when `control-plane-implementation` is present in the analyzed scope.

Consumer contracts, storefronts, AI-assistance repositories, and evidence-only repositories remain eligible for the controls that match their actual responsibilities, but they do not acquire infrastructure lifecycle obligations merely by participating in the product architecture.

The rule remains a scoring `WARNING` when a control-plane implementation exists and no machine-observable status/reconciliation/teardown/lifecycle evidence path is detected.

## Consequences

- Backstage and Composite AI can be evaluated on their real boundaries without artificial Evidence Readiness penalties.
- Infrastructure product implementations remain accountable for lifecycle evidence.
- `NOT_APPLICABLE` continues to mean capability absent, not control satisfied.
- The correction is versioned as `iaap-guard/v0.1.2` so prior `v0.1.1` evidence remains reproducible.
