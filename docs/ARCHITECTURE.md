# IaaP Guard Architecture

## Architectural center

The center of IaaP Guard is the deterministic rule/evidence engine, not GitHub Actions, a GitHub App, a hosted service, or AI.

The system now has three related responsibilities:

1. evaluate the current repository state deterministically;
2. connect explicitly registered repository evidence into one logical product assessment; and
3. compare trustworthy prior Guard evidence with current Guard evidence to determine whether the previous evidence remains supported within Guard's scope.

Adoption Readiness is a diagnostic entry layer around these responsibilities. The
network-free local engine and GitHub adapter share `readiness-report/v1`; they reuse the
existing manifest loader and federation authority rather than duplicating architecture
rules or broadening permissions.

```text
Repository / PR files
        ↓
Component classifier
        ↓
Structured parsers
        ↓
Versioned rule catalog
        ↓
Rule evaluation
        ↓
Normalized result
        ↓
Score + findings
        ↓
scan-result/v1
        ├──────────────────────────────┐
        ↓                              ↓
Evidence Continuity               Product federation (optional)
        ↓                              ↓
evidence-manifest/v1             product-assessment/v1
        ↓                              ↓
continuity/v1                    product-planning-report/v1
```

Adapters consume the same normalized center:

```text
                   ┌─ CLI
IaaP Guard Core ───┼─ GitHub Action
                   └─ GitHub App
```

The adapters distribute the product. They do not own classification, rule semantics, scoring, product relationship semantics, materiality, or continuity semantics.

## Why classification comes first

A global keyword scanner would create structurally wrong findings.

Examples:

- `ProviderConfig` may be valid inside a Crossplane implementation but invalid as a developer-facing product input.
- Terraform/TFE may be a legitimate bootstrap, migration, brownfield, or exception mechanism but should not automatically define the consumer product contract.
- negative fixtures intentionally contain forbidden patterns and must not be reported as live violations.
- documentation may describe a prohibited authority path without granting that authority.
- a Backstage form can be locally valid yet still be incompatible with the canonical product contract stored in another repository.

Therefore rules evaluate **artifact + context**, and product relationship rules evaluate **trusted member artifact + declared role + relationship** rather than token presence alone.

## Classifier contract

The classifier assigns one or more component contexts:

- `consumer-contract`
- `experience`
- `ai-authority`
- `control-plane-implementation`
- `bootstrap`
- `evidence`
- `documentation-fixture`
- `unknown`

Classification must be explainable and included in scan evidence.

## Parser strategy

Prefer structured parsing before textual heuristics:

1. YAML/JSON object structure and known API kinds.
2. JSON Schema/OpenAPI/XRD/CRD property surfaces.
3. Backstage Template parameter and action structure.
4. explicit AI runtime/tool-policy structures.
5. Crossplane Composition/provider structures.
6. Terraform/OpenTofu HCL-aware analysis when introduced.
7. limited text-aware command detection only after context is known.

The scanner must not execute repository code.

## Deterministic core requirements

The core must:

- run without network access;
- require no customer credentials;
- produce the same normalized result for the same inputs and rule version;
- identify the exact ruleset and scoring model used;
- preserve file/location evidence where available;
- generate deterministic evidence digests for normalized evidence records;
- compare prior/current Guard results without inventing hidden authority semantics;
- distinguish Guard-observed material change from authorization/disposition decisions; and
- never grant itself infrastructure or repository mutation authority.

## Repository evidence architecture

The repository scan remains the authoritative architecture evaluation primitive:

```text
repository snapshot
      ↓
scan-result/v1
      ↓
PASS / WARNING / FAIL / NOT_APPLICABLE
```

For the GitHub App, repository scan semantics continue to own the Check conclusion.

## Evidence Continuity architecture

Evidence Continuity is built on normalized Guard results rather than free-form logs.

```text
baseline scan-result/v1 ──┐
                          ├──→ evidence-manifest/v1 ──→ continuity/v1
current scan-result/v1 ───┘
```

The evidence manifest can preserve:

- repository identity and immutable revisions;
- Guard/ruleset/scoring versions;
- current architecture result;
- rule-state transitions;
- introduced and resolved finding evidence;
- deterministic evidence digests;
- Guard-bounded materiality; and
- bounded disposition.

The model deliberately does **not** convert a matching evidence state into a claim of continuing legal, institutional, operational, deployment, compliance, exception, or risk-acceptance authority.

## PR-base continuity architecture

For an IaaP-relevant pull request, the GitHub App derives continuity from two immutable repository snapshots:

```text
GitHub pull request state
        │
        ├── base SHA ──→ safe archive extraction ──→ deterministic scan ──┐
        │                                                                │
        └── head SHA ──→ safe archive extraction ──→ deterministic scan ──┤
                                                                         ↓
                                                              evidence-manifest/v1
                                                                         ↓
                                                                  continuity/v1
                                                                         ↓
                                                       IaaP Guard / Architecture Check
```

The PR head does not choose the baseline. The base SHA is supplied by GitHub pull-request state. A Check rerequest resolves the current PR again and repeats the same bounded process.

Evidence Continuity is advisory. The repository architecture result continues to own `success`, `neutral`, or `failure`; continuity adds `SUPPORTED`, `REVIEW REQUIRED`, or `NOT ESTABLISHED` context without silently creating a new blocking policy.

### Live acceptance

Phase 14 is complete. A fresh deployed-App proof demonstrated `SUPPORTED` on a non-Guard-material change and then `REVIEW REQUIRED` after a controlled Guard-material change on the same pull request, while preserving repository Check conclusion semantics.

Canonical evidence: [`Phase 14 live acceptance`](https://github.com/SAABOLImpactVenture/ai-powered-infrastructure-as-a-product/blob/main/artifacts/phase-14/live-acceptance.json).

## Multi-repository product architecture

Product scope is a separate advisory layer around the triggering repository result.

```text
Trigger repository PR-head scan ───────┐
                                       │
Trusted default-branch product manifest│
                                       ├──→ product-assessment/v1
Reciprocal related-repo manifests ─────┤
                                       │
Related immutable member scans ────────┘
                 ↓
   bounded relationship bundle
                 ↓
       relationship rules
                 ↓
  product-planning-report/v1
```

### Trust comes before federation

The triggering PR cannot expand product membership.

For automatic V1 federation, IaaP Guard:

1. reads `.iaap/product.yaml` from the triggering repository's **default branch**;
2. verifies that the triggering repository registers itself;
3. requires each related repository to be under the same GitHub owner;
4. obtains a separate short-lived related-repository token restricted to `contents:read`;
5. checks that related-repository visibility matches the trigger visibility;
6. reads the related repository's own default-branch manifest;
7. requires the same normalized product identity and membership signature;
8. resolves the related default branch to an immutable commit SHA;
9. scans that immutable snapshot; and
10. discards the token after the stateless invocation.

A required member that cannot satisfy those conditions is missing evidence and makes the product `INCOMPLETE` rather than disappearing from the assessment.

### Bounded relationship evaluation

Member repositories are scanned independently. For V1 relationship rules, Guard builds a separate temporary derivative containing only artifacts classified as `consumer-contract` or `experience`.

That shared relationship bundle is capped at 20 MB. If required evidence is missing or the bundle cannot be built safely, relationship evaluation becomes `INCOMPLETE` and Guard emits product evidence finding `IAP-PR002`.

The initial cross-repository relationship rule is deliberately narrow:

- `IAP-C001` — consumer/storefront constraints must remain compatible with the canonical product contract.

### Live acceptance

Phase 12 is complete. A real two-repository product demonstrated that both members could independently score 100 while trusted federation detected a cross-repository `IAP-C001` incompatibility and failed the logical product at 96. The product Improvement Plan identified targeted work; remediation restored the federated product to SUCCESS 100, followed by a second 100-point primary-member revalidation.

Canonical evidence: [`Phase 12 live federation acceptance`](https://github.com/SAABOLImpactVenture/ai-powered-infrastructure-as-a-product/blob/main/artifacts/phase-12/live-federation-acceptance.json).

## Product-aware Check composition

A registered product-aware pull request can therefore produce three distinct layers in the same GitHub Check:

```text
1. Triggering repository architecture result
2. PR-base Evidence Continuity
3. Multi-repository Product Assessment + optional Product Improvement Plan
```

These layers are intentionally not collapsed into one opaque verdict.

- Repository architecture owns the GitHub Check conclusion.
- Evidence Continuity is advisory temporal evidence.
- Product scope is advisory cross-repository context in V1.

That preserves stable merge semantics while exposing additional governance evidence to accountable humans.

## Adoption architecture and barrier prevention

Several runtime boundaries are product features, not accidental restrictions:

- supported analysis suffixes bound what triggers a full scan;
- archive and extracted-size limits bound untrusted input;
- V1 supports at most 12 registered repositories;
- automatic federation is same-owner and same-visibility only;
- reciprocal default-branch manifests prevent unilateral repository enrollment;
- required missing evidence produces `INCOMPLETE`;
- App access is required on every federated member; and
- no-relevant-change PRs skip the expensive full snapshot path.

See [`ADOPTION-PREREQUISITES.md`](ADOPTION-PREREQUISITES.md) for preflight and troubleshooting guidance.

## GitHub-native progression

### Phase 8 — COMPLETE

The local deterministic core, rule catalog, normalized result contract, fixture matrix, and validation suite were established before distribution infrastructure.

### Phase 9 — COMPLETE

The same core was wrapped by a thin GitHub Action and dogfooded across the six-repository IaaP portfolio. Accepted baselines, repeatability, and critical mutation coverage were frozen under `artifacts/phase-9/`.

### Phase 10 — Public installable beta — COMPLETE

The deterministic core is wrapped by a stateless public GitHub App adapter using narrow GitHub permissions, immutable repository snapshots, bounded input handling, and operator guardrails. The App is deployed, publicly installable, and live-proven.

### Phase 11 — Evidence-to-planning layer — COMPLETE

Deterministic findings can be translated into an advisory, traceable OKR-to-backlog improvement plan without giving Guard work-management or remediation authority.

### Phase 12 — Multi-repository product scope — COMPLETE

Explicit product manifests, reciprocal trust, bounded federation, cross-repository compatibility, product assessment, and product-level planning have been proven against a real two-repository product.

### Phase 13 — Evidence Continuity core — COMPLETE

`evidence-manifest/v1` and deterministic prior/current comparison add evidence digests, rule/finding deltas, Guard-bounded materiality, and continuity/disposition semantics.

### Phase 14 — PR-base Evidence Continuity — COMPLETE

The deployed GitHub App derives the technical baseline from the immutable PR base SHA, compares it with the PR head SHA, and publishes Evidence Continuity in the existing Architecture Check while preserving the existing Check conclusion authority boundary. Both `SUPPORTED` and `REVIEW REQUIRED` live paths have been proven.

### Phase 15 — Adoption Readiness / Preflight — COMPLETE

Deterministic repository preflight, GitHub-aware product diagnostics, and advisory Check
composition are implemented, merged, deployed, and live-accepted through the retained
READY → BLOCKED → READY campaign.

### Phase 16 — Public Beta Closure — COMPLETE

Release status, operational and security controls, adopter reproducibility, support and
rollback procedures, V1 boundaries, and final protected validation are reconciled and
retained without adding product scope.

### Phase 17 — External Adoption Validation — IN PROGRESS

Validate installation, rule quality, usability, and runtime behavior against independent
or unfamiliar infrastructure repositories. Correct defects and material rule-quality
problems, then freeze the V1 rule and output contracts.

### Phase 18 — V1 Product Completion — PLANNED

Publish the bounded V1 release, support and upgrade policies, known limits, final
acceptance evidence, and an explicit completion declaration.

## Canonical V1 boundary

Architecture constraints inherit the complete
[`PRODUCT.md#explicit-exclusions`](PRODUCT.md#explicit-exclusions) boundary. The
architecture does not introduce organizational OKR ingestion, work management,
infrastructure execution, customer infrastructure credentials, persistent customer
state, automated authorization, or cross-organization V1 federation. Context-specific
architecture and adapter notes below narrow implementation authority; they do not expand
the product contract.

## Public App authority

The GitHub App authority remains narrow:

- Metadata read;
- Contents read;
- Pull requests read;
- Checks write;
- no PAT;
- no repository content writes;
- no administration/workflow authority;
- no customer cloud, Kubernetes, Terraform/TFE, or AI credentials.

The triggering-repository installation token is narrowed to the triggering repository. Related product members receive separate short-lived tokens with only `contents:read`.

The reference hosting implementation remains AWS Lambda with a Function URL. Hosting is replaceable and no persistent customer database is required for the current beta.

## Future AI boundary

AI may later explain findings, identify unfamiliar product terminology, summarize evidence changes, or propose remediation. AI-generated interpretation must not alter deterministic rule, product relationship, materiality, or continuity results unless a separately governed future ruleset explicitly introduces that behavior.
