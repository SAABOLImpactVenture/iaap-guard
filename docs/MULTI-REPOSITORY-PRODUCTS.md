# Multi-Repository Infrastructure Products

## Status

**Phase 12 — COMPLETE**

Multi-repository product scope is implemented and live-accepted against a real two-repository Infrastructure-as-a-Product.

Canonical evidence: [`Phase 12 live federation acceptance`](https://github.com/SAABOLImpactVenture/ai-powered-infrastructure-as-a-product/blob/main/artifacts/phase-12/live-federation-acceptance.json).

## Purpose

A real Infrastructure-as-a-Product may span several repositories: a stable product contract, a storefront, a control plane, governance policy, evidence, integration tests, and implementation code can remain independently owned while still forming one logical product.

IaaP Guard V1 therefore supports two complementary scopes:

```text
Repository scope
  → Is this repository demonstrating sound IaaP architecture?

Product scope
  → Do these registered repositories collectively form a coherent IaaP product?
```

Product scope does not replace repository scope. It aggregates repository evidence, evaluates explicitly supported cross-repository relationships, and generates one product-level improvement plan while preserving the exact member repository and path behind every finding.

## What the live proof established

The Phase 12 acceptance campaign used the real **Cloud Foundation Environment** product across:

- `SAABOLImpactVenture/multicloud-foundation-product-poc`; and
- `SAABOLImpactVenture/backstage-infrastructure-product-storefront-poc`.

Both repositories carried the same trusted default-branch `.iaap/product.yaml` membership declaration.

The first federated evaluation produced:

```text
Primary repository architecture: PASS 100
Storefront repository architecture: PASS 100
Evidence completeness: 2/2 repositories
Relationship evaluation: complete
Product relationship finding: IAP-C001
Product conclusion: FAILURE
Product evidence score: 96
```

The finding identified a real contract mismatch: the Backstage storefront's `region` consumer constraints were broader than the canonical product contract.

Guard also generated a product Improvement Plan with:

- 1 Objective;
- 3 Key Results;
- 1 Epic;
- 1 Feature;
- 1 candidate User Story; and
- 4 candidate Tasks.

A targeted storefront PR added the missing `region` min/max constraints. The remediated member then produced **Product SUCCESS 100**, and the primary product repository independently revalidated the complete two-repository product at **SUCCESS 100**.

This is the critical Phase 12 product lesson:

> **Two repositories can each be healthy in isolation while the product relationship between them is wrong.**

Product scope exists to expose that gap.

## Product manifest

A product is registered with `.iaap/product.yaml` using the `iaap-product/v1` contract:

```yaml
schemaVersion: iaap-product/v1
product:
  id: application-platform
  name: Application Platform
  owner: platform-team

repositories:
  - name: acme/platform-contracts
    roles: [product-contract]
    required: true
    primary: true

  - name: acme/backstage-storefront
    roles: [experience]
    required: true

  - name: acme/crossplane-control-plane
    roles: [control-plane]
    required: true

  - name: acme/platform-policies
    roles: [governance]
    required: true

  - name: acme/platform-evidence
    roles: [evidence]
    required: true
```

Supported V1 roles are:

- `product-contract`
- `experience`
- `control-plane`
- `governance`
- `evidence`
- `integration`
- `implementation`
- `other`

V1 supports at most **12 registered repositories** per logical product.

Repository names use `owner/name` form. Each repository has at least one role. Duplicate repository entries are invalid. A product may define at most one `primary: true` repository.

## Reciprocal membership

For automatic GitHub App federation, every participating member repository must carry a trusted default-branch `.iaap/product.yaml` with the same normalized product identity and membership declaration.

Guard compares:

- product `id`;
- product `name`;
- product `owner` when present;
- registered repository names;
- roles;
- `required` flags; and
- `primary` flags.

Best practice is to publish the same manifest file to every member. That reduces drift and makes the intended product boundary easy for humans to inspect.

This reciprocity is intentional. One repository is not allowed to unilaterally enroll another repository merely because IaaP Guard happens to be installed on both.

A pull request may propose a local membership change, but that proposed change does not alter live federation until trusted default-branch membership is established and reciprocated by the participating repositories.

## Product assessment

Each member keeps its normal `scan-result/v1`. IaaP Guard combines compatible member results into `product-assessment/v1`.

The product assessment includes:

- registered and present repositories;
- each member's roles, immutable revision, conclusion, score, and finding count;
- evidence completeness;
- aggregate IaaP dimension coverage;
- overall product evidence score;
- weakest-member score;
- product conclusion;
- repository-qualified findings;
- acquisition mode;
- relationship evaluation status; and
- deterministic `evidenceRevision` derived from the product manifest and member revisions.

### A score cannot hide a failure

Product scoring is intentionally fail-safe.

```text
Repo A: 100 PASS
Repo B: 100 PASS
Repo C:  20 FAIL

Product conclusion: FAILURE
```

The aggregate numeric score remains useful as a coverage indicator, but **a member FAIL cannot be averaged away**.

The live Phase 12 proof also established the inverse-looking but equally important case:

```text
Repo A: 100 PASS
Repo B: 100 PASS
Cross-repo relationship: FAIL

Product conclusion: FAILURE 96
```

Likewise, a required repository that cannot supply trusted evidence produces:

```text
Product conclusion: INCOMPLETE
```

rather than pretending the product is healthy based only on the repositories Guard could see.

## Cross-repository relationship checks

Some IaaP controls cannot be evaluated honestly inside one repository.

V1 assembles reciprocally registered member evidence into a temporary product relationship bundle and reuses the deterministic rule system for relationship semantics.

The initial cross-repository overlay is deliberately narrow:

- `IAP-C001` — consumer/storefront constraints must remain compatible with the canonical product contract.

For example:

```text
platform-contracts
  cloud enum: [aws, gcp]

backstage-storefront
  cloud enum: [aws, azure]

IaaP Guard product finding
  IAP-C001
  storefront accepts azure but canonical product contract does not
```

The finding remains traceable to the member repository and file that exposed the incompatibility.

V1 does **not** blindly rerun every repository rule across the combined bundle. A control is promoted to product-relationship scope only when its semantics genuinely support cross-repository evaluation. That avoids double-counting repository controls or silently changing existing rule meaning.

## Bounded relationship evidence

Member repositories are scanned independently from their complete bounded snapshots. Guard does not keep every extracted member repository in a second shared copy merely to evaluate relationships.

For the V1 `IAP-C001` relationship pass, Guard builds a separate temporary derivative containing only artifacts already classified as:

- `consumer-contract`; or
- `experience`.

That relationship bundle has a cumulative **20 MB** limit across the logical product.

If required member evidence is unavailable, relevant artifacts cannot be copied safely, or the relationship bundle exceeds its bound, Guard records relationship evaluation as **INCOMPLETE** and adds product evidence finding `IAP-PR002`.

Guard does not crash the webhook, omit the relationship silently, or present an unevaluated relationship as green.

The product assessment records its evidence-acquisition mode so machine consumers can distinguish:

- `provided-evidence` — member `scan-result/v1` documents were supplied to the CLI and no related repository content was fetched; and
- `trusted-github-federation` — the GitHub App read reciprocally registered member repositories using bounded repository-scoped access.

## Product-level OKR improvement plan

A `product-assessment/v1` can feed `product-planning-report/v1`:

```text
Member evidence
      ↓
Product assessment
      ↓
Objectives
      ↓
Measurable Key Results
      ↓
Epics mapped to KRs
      ↓
Features
      ↓
Candidate User Stories
      ↓
Candidate Tasks
      ↓
Acceptance Evidence
```

The planning layer is still advisory. It does not assign people, manage sprints, estimate capacity, create work autonomously, or execute remediation.

The Phase 12 live proof demonstrated this path against an actual cross-repository incompatibility, then used the smallest targeted contract correction to move the product from FAILURE 96 to SUCCESS 100.

## CLI evidence aggregation

When member `scan-result/v1` files are already available, product evidence can be aggregated without GitHub federation:

```bash
PYTHONPATH=src python3 -m iaap_guard.cli product-assess \
  .iaap/product.yaml \
  evidence/contracts.json \
  evidence/storefront.json \
  evidence/control-plane.json
```

Generate the product-level improvement plan:

```bash
PYTHONPATH=src python3 -m iaap_guard.cli product-plan \
  .iaap/product.yaml \
  evidence/contracts.json \
  evidence/storefront.json \
  evidence/control-plane.json
```

Use `--format json` for the normalized machine-readable contracts.

The CLI commands above aggregate already-produced member evidence. They do **not** fetch related repositories or reconstruct cross-repository artifact relationships from JSON alone. The GitHub product-aware runtime performs the additional temporary member-bundle step needed for `IAP-C001` relationship evaluation.

## GitHub App trust model

Cross-repository access creates a different security problem from ordinary repository scanning. V1 uses explicit boundaries rather than broad organization-wide crawling.

### Product membership is trusted configuration

The triggering pull request is **not allowed to define or expand product membership**.

When a product-aware Check runs, IaaP Guard reads `.iaap/product.yaml` from the triggering repository's **default branch**. A PR that adds another repository to its own copy of the manifest cannot cause Guard to read that repository.

Before a related repository's content becomes product evidence, Guard reads that repository's own default-branch manifest and requires the same normalized product identity and membership declaration.

### Related repositories remain least privilege

For each candidate related repository, Guard:

1. verifies that the GitHub App is installed with access to that repository;
2. creates a short-lived installation token restricted to that single repository;
3. requests only `contents:read` for that related-repository token;
4. reads the related repository's trusted default-branch product manifest;
5. requires reciprocal product identity and membership;
6. resolves the repository's default branch to an immutable commit SHA;
7. scans that immutable snapshot; and
8. discards the token after the stateless invocation.

The existing triggering-repository token and App permission contract are not broadened.

### V1 federation boundaries

To prevent product output from becoming an accidental information bridge, V1 automatically federates only repositories that:

- are explicitly registered in the triggering repository's trusted manifest;
- reciprocally register the same product identity and membership on their own trusted default branch;
- are under the same GitHub owner/organization as the triggering repository;
- have the same visibility as the triggering repository; and
- are accessible through an IaaP Guard installation.

A required member that fails those conditions is represented as missing evidence and makes the product **INCOMPLETE**. Guard does not silently omit it and call the product complete.

## Snapshot semantics

A product-aware pull-request evaluation uses:

```text
Triggering repository
  → immutable PR-head SHA for architecture evaluation
  → default branch for trusted membership

Related repositories
  → default branch for reciprocal membership
  → immutable current default-branch SHAs for architecture evidence
```

The resulting product assessment carries an `evidenceRevision` so the exact multi-repository evidence set can be distinguished from a later assessment after one of the member repositories changes.

This is not a claim that all repositories changed atomically. It is an explicit, reproducible description of the evidence set Guard evaluated at that moment.

## Interaction with Evidence Continuity

The GitHub App preserves both layers:

```text
Triggering repository architecture
        +
PR-base Evidence Continuity
        +
Multi-repository Product Assessment
        +
Product Improvement Plan when needed
```

The triggering repository's base/head comparison remains repository-scoped in the current contract. Product-wide temporal continuity across changing member revisions may evolve separately if customer value justifies the added complexity.

## GitHub Check behavior

The existing Check remains:

```text
IaaP Guard / Architecture
```

For a repository that is not registered as a product member, behavior remains the repository-only flow.

For a reciprocally registered member, the Check adds a **Product Assessment** and **Product Improvement Plan** beneath the repository result and preserves the repository Evidence Continuity section.

V1 intentionally keeps the **triggering repository result authoritative for the Check's GitHub conclusion**. The product section is advisory context. This avoids turning a PR in one repository into a blocking failure because another repository already had an unrelated issue.

A future product-specific blocking Check could be introduced as a separate, explicit contract after product owners have enough evidence to decide that cross-repository product health should become a merge gate.

## Adoption prerequisites and common failure modes

Before enabling product federation, read [`ADOPTION-PREREQUISITES.md`](ADOPTION-PREREQUISITES.md).

The most common barriers are:

- manifest exists only on the PR branch, not the trusted default branch;
- reciprocal manifests do not declare the same normalized product boundary;
- the App is not installed with access to a required member;
- member repositories have different visibility;
- a related repository is under a different owner;
- a required repository has no resolvable default branch;
- the logical product exceeds 12 repositories;
- repository snapshots exceed beta bounds; or
- the relationship derivative exceeds the 20 MB product bundle limit.

Those conditions should produce no product section or `INCOMPLETE`, not pressure to grant Guard broader permissions.

## Product boundary

Product scope still does not make IaaP Guard a provisioning system, portfolio manager, ticketing system, sprint manager, or infrastructure control plane.

Its bounded job is:

> **Evaluate whether infrastructure is being engineered as a product, connect evidence across the explicitly declared product boundary, detect supported cross-repository relationship drift, and translate demonstrated gaps into an actionable but advisory improvement plan.**
