# Deterministic Core

## Purpose

The deterministic core turns the IaaP Guard product contract into executable architecture evaluation and reconstructable evidence without introducing cloud credentials, Kubernetes credentials, AI inference, remediation authority, or a persistent customer database.

The core now produces two related contracts:

```text
files
  ↓
safe loader
  ↓
context classifier
  ↓
structured rule evaluators
  ↓
rule results + findings
  ↓
coverage/v1 scoring
  ↓
scan-result/v1
  ↓
evidence-manifest/v1
  ↓
continuity/v1
```

`scan-result/v1` describes the current Guard-observed architecture state. `evidence-manifest/v1` can compare that state with a prior trustworthy Guard result and record whether the prior evidence remains supported within Guard's deterministic scope.

## Safety boundary

The core reads files and normalized Guard evidence only. It does not:

- import scanned Python modules;
- execute shell scripts;
- execute Terraform/OpenTofu;
- call kubectl/Helm;
- call cloud APIs;
- access GitHub APIs;
- access repository secrets;
- modify the scanned repository;
- grant or revoke authorization;
- approve exceptions or risk acceptance; or
- decide deployment/disposition authority.

Generated/output directories and common dependency/vendor directories are excluded from traversal. Files larger than the bounded input size are skipped rather than executed or streamed to another service.

## Classification

The classifier recognizes:

- Crossplane XRDs and explicit product schemas as `consumer-contract`;
- Backstage Software Templates and explicit storefront contracts as `experience`;
- explicit AI runtime/tool authority structures as `ai-authority`;
- Crossplane Compositions, ProviderConfigs, provider objects, implementation inventories, reconciliation ownership records, and Terraform/OpenTofu/HCL files as `control-plane-implementation`;
- minimal seed/bootstrap evidence as `bootstrap`;
- tests, deterministic validation/verification scripts, workflows, and evidence records as `evidence`;
- documentation as `documentation-fixture`;
- otherwise `unknown`.

Fixture metadata can explicitly override context only inside the repository's test fixtures. That allows a bad example to be evaluated as the architecture context it represents instead of being suppressed merely because it lives under `fixtures/`.

## Rule implementation notes

### IAP-P001 — implementation leakage

Uses consumer-facing property surfaces after context classification. ProviderConfig or Terraform terminology in control-plane implementation does not trigger this rule.

### IAP-P002 — lifecycle ownership

Detects consumer-facing lifecycle fields such as deletion/orphan/retention policy controls.

### IAP-X001 — experience authority

Detects direct infrastructure execution actions in an experience layer. A GitHub pull-request publication action remains a valid order/proposal handoff.

### IAP-A001 — AI infrastructure authority

Evaluates explicit runtime booleans and allowed tool lists. Dangerous names in deny-lists do not grant authority and therefore do not fail the rule.

### IAP-A002 — accountable authorization

Requires deterministic evidence of self-approval, self-merge, explicit approval bypass, or proposal mode with human approval disabled. It does not infer bypass from ordinary automation alone.

### IAP-C001 — contract compatibility

Compares a recognizable canonical product schema with a recognizable storefront/order schema. Guard evaluates deterministic compatibility evidence only; without a recognizable pair, the rule is `NOT_APPLICABLE` rather than guessed.

### IAP-P003 — product abstraction

Warns when control-plane implementation is present in analyzed scope with no recognizable product contract. Bootstrap-only scope is excluded.

### IAP-P004 — product ownership

Requires owner/team-equivalent accountability metadata in the product contract's required surface.

### IAP-G001 — deterministic validation

Looks for independently executable test/validation/verification paths or explicit product-boundary validation evidence. CI existence alone is not treated as sufficient evidence.

### IAP-E001 — lifecycle/evidence path

Looks for machine-observable status structures and explicit reconciliation, teardown, orphan, runtime-validation, or evidence paths.

### IAP-CX01 — authoritative reconciler conflict

Guard is deliberately conservative. It only evaluates when structured reconciliation ownership evidence exists. Technology coexistence alone does not produce a finding. This rule remains experimental and non-scoring.

## Scoring

Only applicable scoring rules participate in `coverage/v1`.

```text
dimension = PASS / applicable scoring controls × 100
overall   = equal-weight mean of applicable dimension scores
```

`WARNING` and `FAIL` are unsatisfied controls. `NOT_APPLICABLE` is excluded. Experimental/non-scoring results never affect score or conclusion.

## Conclusion mapping

- any scoring `FAIL` → `failure`
- no scoring FAIL and at least one scoring `WARNING` → `neutral`
- otherwise → `success`

These are point-in-time architecture conclusions. They do not state whether an infrastructure action is authorized to execute.

## Evidence Continuity contract

Evidence Continuity compares a prior normalized Guard result with a current normalized Guard result.

The core can preserve:

- baseline and current repository identity;
- immutable revisions when supplied;
- Guard/rule-catalog/scoring versions;
- rule-state transitions;
- introduced and resolved finding evidence;
- deterministic evidence digests;
- Guard-bounded materiality; and
- bounded revalidation disposition.

The normalized continuity states are:

- `supported`
- `review_required`
- `not_established`

### `supported`

The current and baseline Guard evidence differ in revision or other non-material metadata, but Guard detects no rule/finding change that its continuity model classifies as material.

This means **Guard can support continuity of its own evidence**, not that an external authorization remains valid.

### `review_required`

Guard detects a material rule/finding transition or evidence delta that means the prior Guard evidence should not be silently treated as still applicable.

This is a decision-support signal. It does not choose the reviewer, approval authority, exception owner, or final disposition.

### `not_established`

Guard does not have a suitable prior result from which to establish continuity.

## Deterministic evidence digest

Evidence manifests use canonicalized normalized evidence to derive SHA-256 digests. The digest is intended to make evidence records comparable and tamper-evident within the Guard contract.

A digest is **not** a digital authorization signature, legal attestation, or proof that an external system actually executed the described infrastructure action.

## GitHub PR baseline semantics

The core itself is transport-neutral: callers provide baseline/current normalized Guard results.

The GitHub App adapter adds a trusted baseline rule:

```text
PR base SHA → deterministic scan → baseline scan-result/v1
PR head SHA → deterministic scan → current scan-result/v1
                                ↓
                      evidence-manifest/v1
```

The PR head cannot choose the base SHA. GitHub pull-request state supplies it.

## Current limitations

IaaP Guard intentionally does not attempt full semantic HCL parsing, live reconciler discovery, compliance determinations, legal authorization evaluation, autonomous exception handling, historical SaaS analytics, or AI-assisted verdicts.

Multi-repository product scope is bounded by explicit reciprocal registration and narrow GitHub read authority. Repository-level Evidence Continuity currently compares Guard-observed base/head states; product-wide temporal continuity may evolve separately if customer value justifies the complexity.

These limits preserve the product boundary: **deterministic architecture evidence first, accountable human governance above it.**
