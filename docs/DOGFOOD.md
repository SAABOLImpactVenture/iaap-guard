# Phase 9 Dogfood Evidence Plan

## Portfolio

Dogfood IaaP Guard against these six repositories as one bounded product system:

1. `SAABOLImpactVenture/ai-powered-infrastructure-as-a-product`
2. `SAABOLImpactVenture/backstage-infrastructure-product-storefront-poc`
3. `SAABOLImpactVenture/crossplane-multicloud-seed-poc`
4. `SAABOLImpactVenture/multicloud-foundation-product-poc`
5. `SAABOLImpactVenture/composite-ai-infrastructure-product-poc`
6. `SAABOLImpactVenture/multicloud-foundation-poc-integration`

## Purpose

Dogfood must prove value by evidence rather than by asserting that the rules look reasonable.

## Baseline expectations

The current known-good default branches should scan without unexplained critical failures. Different repository responsibilities should produce different applicability profiles rather than being forced toward one universal repository shape.

Examples:

- the program/thesis repository may have many product-runtime rules `NOT_APPLICABLE`;
- the seed repository must not be penalized for intentionally lacking consumer product APIs;
- the product repository may legitimately contain ProviderConfigs and provider resources behind the consumer contract;
- the AI repository may mention denied tools and unsafe scenarios in policies/tests without those references becoming authority violations;
- the integration repository intentionally contains negative cases and forbidden-token verification logic.

## Required intentional mutations

Dogfood fixtures and controlled PRs must include:

1. good product contract;
2. Terraform workspace exposed to a consumer;
3. ProviderConfig exposed to a consumer;
4. Backstage/experience layer directly provisioning;
5. AI apply authority;
6. consumer-selectable lifecycle policy;
7. missing ownership metadata;
8. possible product/reconciler conflict;
9. missing/bypassed approval path;
10. missing evidence/validation path;
11. storefront accepted domain broader than the canonical product contract.

## False-positive controls

Guard must explicitly prove it does **not** fail merely because:

- `ProviderConfig` appears in control-plane implementation;
- Terraform/TFE appears in an implementation, migration, comparison, bootstrap, or exception context;
- a negative fixture contains a forbidden token;
- documentation describes a prohibited action;
- an AI deny-list contains names of dangerous tools.

## Success criteria

Phase 9 succeeds when:

- all six repositories scan without scanner error;
- current known-good main branches have zero unexplained critical `FAIL` results;
- every intentional critical mutation is detected with the expected stable rule ID;
- the positive false-positive controls remain non-failing;
- same commit + same rule catalog + same scoring model produces the same normalized result;
- no repository code is executed by the scanner;
- no cloud, Kubernetes, Terraform/TFE, AI or customer credentials are required;
- each finding includes component context, path/location when available, deterministic evidence and a recommendation;
- measured false positives are recorded rather than silently suppressed.

## Evidence bundle

```text
artifacts/phase-9/
├── portfolio-baseline.json
├── fixture-matrix.json
├── expected-vs-actual.json
├── false-positive-analysis.json
├── repeatability.json
└── dogfood-scorecard.json
```

## Exit gate

Do not deploy the externally installable GitHub App until the deterministic engine and dogfood evidence establish that Guard finds meaningful IaaP architecture issues with an acceptable false-positive profile.
