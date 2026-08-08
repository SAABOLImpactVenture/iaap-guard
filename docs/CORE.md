# Deterministic Core — Phase 8

## Purpose

The deterministic core turns the Phase 8 product contract into executable architecture evaluation without introducing GitHub App infrastructure, cloud credentials, Kubernetes credentials, AI inference, or remediation authority.

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
```

## Safety boundary

The core reads files only. It does not:

- import scanned Python modules;
- execute shell scripts;
- execute Terraform/OpenTofu;
- call kubectl/Helm;
- call cloud APIs;
- access GitHub APIs;
- access repository secrets;
- modify the scanned repository.

Generated/output directories and common dependency/vendor directories are excluded from traversal. Files larger than the V0 bounded input size are skipped rather than executed or streamed to another service.

## V0 classification

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

## V0 rule implementation notes

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

Compares a recognizable canonical product schema with a recognizable storefront/order schema. V0 evaluates enum containment, min/max string constraints, and patterns. Without a deterministic pair, the rule is `NOT_APPLICABLE` rather than guessed.

### IAP-P003 — product abstraction

Warns when control-plane implementation is present in analyzed scope with no recognizable product contract. Bootstrap-only scope is excluded.

### IAP-P004 — product ownership

Requires owner/team-equivalent accountability metadata in the product contract's required surface.

### IAP-G001 — deterministic validation

Looks for independently executable test/validation/verification paths or explicit product-boundary validation evidence. CI existence alone is not treated as sufficient evidence.

### IAP-E001 — lifecycle/evidence path

Looks for machine-observable status structures and explicit reconciliation, teardown, orphan, runtime-validation, or evidence paths.

### IAP-CX01 — authoritative reconciler conflict

V0 is deliberately conservative. It only evaluates when structured reconciliation ownership evidence exists. Technology coexistence alone does not produce a finding. This rule remains experimental and non-scoring.

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

## Current limitations

V0 intentionally does not attempt full semantic HCL parsing, organization-wide cross-repository relationship discovery, live reconciler discovery, compliance mapping, or AI-assisted inference. Those capabilities require evidence that they improve customer value enough to justify additional complexity.

Phase 9 dogfood will determine which classifier/rule gaps are real before the rule engine expands.
