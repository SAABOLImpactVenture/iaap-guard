# IaaP Guard

> **IaaS is what you buy. Infrastructure-as-a-Product is what you build. IaaP Guard makes sure you keep building it that way.**

IaaP Guard is a GitHub-native architecture and product-governance system that evaluates whether infrastructure is actually being engineered as a product.

## Phase 8 boundary

The first product is intentionally small: a deterministic, stateless repository/PR evaluator with a reusable local core. It does **not** provision infrastructure, connect to customer clouds or Kubernetes clusters, run Terraform/TFE, remediate changes, or compete with generic security scanners.

```text
Repository / PR files
        ↓
Component classifier
        ↓
Structured deterministic parsers
        ↓
Versioned IaaP rule catalog
        ↓
Normalized findings
        ↓
Coverage-based maturity score
        ↓
JSON + human-readable result
```

The same core can later be wrapped by:

```text
IaaP Guard Core
   ├── CLI
   ├── GitHub Action     # dogfood
   └── GitHub App        # distribution
```

The adapter is not the product. The durable product IP is the system of IaaP product knowledge, rules, evidence, compatibility, and operating model.

## V0 principles

- Product over tooling.
- Stable consumer contracts.
- Replaceable experience layer.
- Bounded intelligence.
- Deterministic governance.
- Human authorization.
- Evidence first.
- One authoritative reconciler.
- Least privilege.
- Context-aware analysis rather than naive keyword grep.
- Minimum effort first.

## Phase 8 contents

- `docs/PRODUCT.md` — product definition and explicit V0 exclusions.
- `docs/ARCHITECTURE.md` — smallest useful core and future adapter boundary.
- `docs/RULE-CATALOG.md` — V0 deterministic rule semantics.
- `docs/SCORING.md` — transparent coverage-based maturity model.
- `docs/DOGFOOD.md` — Phase 9 six-repository evidence plan.
- `adr/` — architecture decisions for deterministic-first, context-aware analysis.
- `rules/catalog.yaml` — machine-readable V0 rule catalog.
- `schemas/scan-result.schema.json` — normalized result contract.
- `fixtures/` — positive and negative architecture cases.

## Current status

**PHASE 8 — IaaP Guard Product Definition: IN PROGRESS**

This repository does not yet contain the scanner runtime or GitHub App infrastructure. Those are deliberately gated behind the Phase 8 product contract and evidence fixtures.
