# IaaP Guard V1 Contract Freeze

## Status

**FROZEN for V1 as of Phase 17.**

This document freezes the public compatibility and authority surface that Phase 18 will
publish. A backward-incompatible change requires an explicitly versioned successor and
must not silently change V1 behavior.

## Frozen contracts

| Contract area | Frozen V1 authority |
|---|---|
| Repository result | `scan-result/v1` |
| Rule catalog | `iaap-guard/v0.1.2` |
| Scoring | `coverage/v1` |
| Evidence continuity | `evidence-manifest/v1` and `continuity/v1` |
| Repository planning | `planning-report/v1` |
| Planning catalog | `iaap-planning/v0.1.0` |
| Product registration | `iaap-product/v1` |
| Product assessment | `product-assessment/v1` |
| Product planning | `product-planning-report/v1` |
| Adoption readiness | `readiness-report/v1` |
| GitHub App authority | `config/github-app-v0.json` |
| External campaign | `external-adoption/v1` |

The corresponding JSON Schemas under `schemas/`, the public planning catalog at
`planning/catalog.yaml`, and the authority configuration are the public
machine-readable sources of truth. The planning catalog is frozen at
`iaap-planning/v0.1.0` and immutable public Git blob
`9f63a1462a9c2acd7db387990caf10f612a40b8b`, with SHA-256
`e8e21f08c78b071b8300c25ccadd661396c77c7ae6bce048ff12b9255cba7a1d`. The versioned
rule-catalog identifier is public; rule implementation is maintained privately.

## Compatibility policy

V1 permits:

- defect fixes that preserve documented semantics;
- additive documentation and examples;
- new adapters that consume the same deterministic contracts without redefining them;
- security and dependency updates that do not change authority; and
- additive optional fields only when existing valid V1 documents and consumers remain
  valid and deterministic.

V1 does not permit silently changing rule meaning, score calculation, conclusion
authority, required fields, membership trust, evidence continuity semantics, or GitHub
App permissions. A planning-catalog mapping must not change under
`iaap-planning/v0.1.0`; a semantic change requires a new catalog version and migration
guidance. Other backward-incompatible changes likewise require a new contract version.

## Frozen authority boundary

The freeze incorporates
[`PRODUCT.md#explicit-exclusions`](PRODUCT.md#explicit-exclusions). It does not add
organizational OKR ingestion, enterprise strategy or work management, infrastructure
execution, customer infrastructure credentials, repository mutation, automated
remediation or authorization, persistent customer analytics, cross-organization V1
federation, Marketplace billing, compliance authority, or production-readiness claims.

## Support implication

Phase 18 may package, document, tag, and support these contracts. It may not reopen them
to broaden IaaP Guard into capabilities reserved for separate products.
