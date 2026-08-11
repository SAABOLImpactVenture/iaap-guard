# IaaP Guard Architecture

## Architectural center

The center of IaaP Guard is the deterministic rule/evidence engine, not GitHub Actions, a GitHub App, a hosted service, or AI.

The engine now has two tightly related responsibilities:

1. evaluate the current repository/product state deterministically; and
2. compare trustworthy prior Guard evidence with current Guard evidence to determine whether the previous evidence remains supported within Guard's scope.

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
        ↓
Evidence manifest
        ↓
Prior/current comparison
        ↓
continuity/v1
```

Adapters consume the same normalized core:

```text
                   ┌─ CLI
IaaP Guard Core ───┼─ GitHub Action
                   └─ GitHub App
```

The adapters distribute the product. They do not own rule semantics, scoring, materiality, or continuity semantics.

## Why classification comes first

A global keyword scanner would create structurally wrong findings.

Examples:

- `ProviderConfig` may be valid inside a Crossplane implementation but invalid as a developer-facing product input.
- Terraform/TFE may be a legitimate bootstrap, migration, brownfield or exception mechanism but should not automatically define the consumer product contract.
- negative fixtures intentionally contain forbidden patterns and must not be reported as live violations.
- documentation may describe a prohibited authority path without granting that authority.

Therefore rules evaluate **artifact + context**, not token presence alone.

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

## Evidence architecture

Evidence Continuity is built on normalized Guard results rather than on free-form logs.

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
- a bounded disposition such as `revalidation_required`.

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

The PR head does not choose the baseline. The base SHA is supplied by GitHub pull-request state. A Check rerequest resolves the current PR and repeats the same bounded process.

Evidence Continuity is advisory in the current GitHub App contract. The repository architecture result continues to own `success`, `neutral`, or `failure`; continuity adds `SUPPORTED`, `REVIEW REQUIRED`, or `NOT ESTABLISHED` context without silently creating a new blocking policy.

## Multi-repository product scope

Product scope remains a separate advisory layer around the triggering repository result. Related repositories participate only through explicit trusted product registration, reciprocal membership, compatible owner/visibility boundaries, and repository-scoped read authority.

```text
Trigger repository scan ───────┐
Related trusted repo scans ────┼──→ product-assessment/v1
                               └──→ product-planning-report/v1
```

The product-aware runtime must preserve the repository Evidence Continuity section when it enriches the GitHub Check with product-level context.

## GitHub-native progression

### Phase 8 — COMPLETE

The local deterministic core, rule catalog, normalized result contract, fixture matrix, and validation suite were established before distribution infrastructure.

### Phase 9 — COMPLETE

The same core was wrapped by a thin GitHub Action and dogfooded across the six-repository IaaP portfolio. Accepted baselines, repeatability, and critical mutation coverage were frozen under `artifacts/phase-9/`.

### Phase 10 — Public installable beta

The deterministic core is wrapped by a stateless public GitHub App adapter using narrow GitHub permissions and immutable repository snapshots.

### Phase 11 — Evidence-to-planning layer — COMPLETE

Deterministic findings can be translated into an advisory, traceable OKR-to-backlog improvement plan without giving Guard work-management or remediation authority.

### Phase 12 — Multi-repository product scope

Explicit product manifests, reciprocal trust, bounded federation, product assessment, and product-level planning extend Guard from repositories to logical infrastructure products.

### Phase 13 — Evidence Continuity core — COMPLETE

`evidence-manifest/v1` and deterministic prior/current comparison add evidence digests, rule/finding deltas, Guard-bounded materiality, and continuity/disposition semantics.

### Phase 14 — PR-base Evidence Continuity

The GitHub App derives the technical baseline from the immutable PR base SHA, compares it with the PR head SHA, and publishes Evidence Continuity in the existing Architecture Check while preserving the existing Check conclusion authority boundary.

## Public App authority

The GitHub App authority remains narrow:

- Metadata read;
- Contents read;
- Pull requests read;
- Checks write;
- installation token narrowed to the triggering repository;
- no PAT;
- no repository content writes;
- no administration/workflow authority;
- no customer cloud, Kubernetes, Terraform/TFE, or AI credentials.

The reference hosting implementation remains AWS Lambda with a Function URL. Hosting is replaceable and no persistent customer database is required for the current beta.

## Future AI boundary

AI may later explain findings, identify unfamiliar product terminology, summarize evidence changes, or propose remediation. AI-generated interpretation must not alter deterministic rule, materiality, or continuity results unless a separately governed future ruleset explicitly introduces that behavior.
