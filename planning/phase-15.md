# Phase 15 — Adoption Readiness / Preflight

## Status

**COMPLETE — implemented, merged, deployed, live-accepted, and backed by retained evidence.**

Phase 15 adds a deterministic `readiness-report/v1` diagnostic layer that answers
whether Guard can meaningfully evaluate the intended repository or registered product
scope. It does not add architecture rules, authorization, remediation, or infrastructure
execution.

## Frozen scope

The implementation provides:

- a network-free local repository readiness engine;
- strict `schemas/readiness-report.schema.json` validation;
- `preflight <path> --repository owner/name --format markdown|json --output ...`;
- GitHub-aware product readiness built on the existing repository-scoped App runtime;
- stable `IAP-RDYxxx` requirement identifiers and actionable diagnostics;
- advisory Product Readiness rendering in the existing Architecture Check; and
- deterministic ordering with no timestamps in the normalized report.

## Preserved boundaries

- `.iaap/product.yaml` remains optional for a normal single repository.
- Existing `iaap-product/v1` validation and normalized membership semantics are reused.
- Architecture scoring and `success` / `neutral` / `failure` Check conclusions remain
  authoritative and unchanged.
- `coverage/v1`, `continuity/v1`, and `product-assessment/v1` semantics remain unchanged.
- Readiness is diagnostic and advisory; it is not an authorization decision.
- Local preflight makes no network calls and never executes scanned code.
- GitHub authority remains Metadata read, Contents read, Pull requests read, Checks
  write. Related repositories retain narrow per-repository `contents:read` tokens.
- No PATs, organization administration, repository writes, workflow permissions,
  infrastructure credentials, persistent customer database, or automatic remediation.
- V1 remains bounded to 12 product members, existing repository/archive limits, and the
  existing relationship-evidence bundle limit.

## Readiness model

Reports use `READY`, `READY_WITH_ADVISORIES`, `BLOCKED`, and `NOT_APPLICABLE` where a
requirement is outside the evaluated mode. Every non-ready requirement records its
observed state, impact, remediation, severity/blocking classification, and applicable
repository/path. Required members can block product readiness; unavailable optional
members produce advisories where existing product semantics allow it.

Repository preflight validates path/readability, supported analyzable artifacts,
per-file bounds, and an optional product manifest. Registered local products are ready
for local validation when the manifest is valid and self-registering; GitHub-only trust,
access, visibility, reciprocity, immutable revision, and acquisition checks are reported
as explicitly unevaluated until the GitHub-aware adapter runs.

GitHub-aware preflight diagnoses the same trust/acquisition barriers already enforced by
product federation before users mistake missing evidence for product health.

## Validation contract

Automated coverage includes ordinary single repositories, minimal/no evidence,
malformed and invalid registration, duplicate/oversized/multiple-primary membership,
self-membership, valid local registration, inaccessible/visibility-mismatched/missing or
non-reciprocal GitHub members, complete products, optional-member advisory behavior,
unchanged Check conclusions, and continuity-preserving rendering. The complete existing
Phase 8–14 suite remained green.

## Live acceptance completed

The deployed runtime completed the required non-destructive sequence:

1. a correctly configured registered product reported `READY`, with normal Product
   Assessment;
2. a controlled non-reciprocal required member reported actionable `BLOCKED` with
   `IAP-RDY106`, without broader permissions and without changing the Architecture Check
   conclusion; and
3. restoring the exact reciprocal manifest returned the same product to `READY`, after
   which normal Product Assessment proceeded again.

Deployment and acceptance evidence are retained in the program hub at
`artifacts/phase-15/acceptance-campaign.json`, merged as commit
`4035993fee32cb58a8d9ca6edab8810a489514da`.
