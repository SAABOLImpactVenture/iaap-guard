# IaaP Guard V0 Rule Catalog

Rule catalog version: `iaap-guard/v0.1.2`

## Rule design requirements

Every rule has:

- a stable rule ID;
- a dimension;
- explicit applicability contexts;
- a default failing result (`FAIL` or `WARNING`);
- deterministic evidence requirements;
- remediation guidance;
- whether it participates in scoring.

A rule must return `NOT_APPLICABLE` when its required architectural capability is not present.

## V0 rules

### IAP-P001 — Consumer contract exposes implementation machinery

**Dimension:** Consumer Boundary  
**Applies to:** `consumer-contract`, `experience`  
**Violation:** `FAIL`

Fail when a consumer-facing product definition exposes implementation topology such as ProviderConfig selection, Composition selection, Terraform/TFE workspace/module controls, raw provider versions, direct Kubernetes namespaces used as implementation controls, raw IAM policy, or equivalent provider machinery that should remain platform-owned.

Implementation-layer use of these technologies is not itself a failure.

### IAP-P002 — Consumer controls platform lifecycle policy

**Dimension:** Consumer Boundary  
**Applies to:** `consumer-contract`, `experience`  
**Violation:** `FAIL`

Fail when a consumer can select managed-resource lifecycle behavior such as deletion/orphan policy that the platform product is expected to own.

### IAP-X001 — Experience layer directly provisions infrastructure

**Dimension:** Experience / Authority  
**Applies to:** `experience`  
**Violation:** `FAIL`

Fail when a storefront, portal, Backstage template or equivalent consumer experience directly invokes infrastructure apply/delete/provision operations rather than submitting bounded product intent into the governance chain.

Creating a reviewable order/proposal PR is not direct infrastructure provisioning.

### IAP-A001 — AI receives infrastructure execution or credential authority

**Dimension:** Experience / Authority  
**Applies to:** `ai-authority`  
**Violation:** `FAIL`

Fail when AI is granted direct apply/delete, cloud-admin, Kubernetes-admin, credential/secret access, Terraform/TFE run authority, or equivalent unrestricted infrastructure execution capability.

### IAP-A002 — AI or automation bypasses accountable human approval

**Dimension:** Governance  
**Applies to:** `ai-authority`, `experience`, `evidence`  
**Violation:** `FAIL`

Fail when architecture or runtime policy explicitly permits an AI/automation path to self-approve, merge its own material infrastructure proposal, or bypass the declared human authorization boundary.

### IAP-C001 — Consumer accepted domain is broader than canonical product API

**Dimension:** Consumer Boundary  
**Applies to:** paired `experience` + `consumer-contract`  
**Violation:** `FAIL`

Fail when a storefront/order contract permits values or constraints outside the canonical product API. Examples include broader cloud/region enums, weaker minimum constraints, broader maximum constraints, or incompatible patterns.

Return `NOT_APPLICABLE` when both sides of the contract cannot be identified.

### IAP-P003 — Infrastructure implementation lacks a recognizable product abstraction

**Dimension:** Product Abstraction  
**Applies to:** `control-plane-implementation`  
**Violation:** `WARNING`

Warn when substantial infrastructure implementation is present but no stable consumer/product abstraction can be identified in the analyzed scope.

Bootstrap-only repositories are exempt unless they claim to expose consumer products.

### IAP-P004 — Product lacks accountable ownership metadata

**Dimension:** Product Abstraction  
**Applies to:** `consumer-contract`  
**Violation:** `WARNING`

Warn when a product contract has no required owner/team/accountability metadata or equivalent organization-defined ownership field.

The V0 reference terms are `owner` or `team`; configuration of additional enterprise aliases is future work.

### IAP-G001 — Governed change lacks deterministic validation evidence

**Dimension:** Governance  
**Applies to:** product-bearing `consumer-contract`, `experience`, `control-plane-implementation`  
**Violation:** `WARNING`

Warn when a product-bearing repository has no recognizable deterministic validation/test path for the architecture contract being changed.

The mere presence of CI is not sufficient if it does not validate the relevant product boundary.

### IAP-E001 — Product implementation lacks status/evidence/lifecycle path

**Dimension:** Evidence Readiness  
**Applies to:** `control-plane-implementation`  
**Violation:** `WARNING`

Warn when an infrastructure product implementation has no recognizable status, evidence, reconciliation-result, teardown, or lifecycle verification path appropriate to the analyzed architecture.

A consumer contract, storefront, Composite AI assistant, or evidence-only repository does not acquire a reconciliation/lifecycle obligation merely because it participates in the product architecture. V0 requires actual `control-plane-implementation` context before this rule is applicable.

### IAP-CX01 — Possible multiple authoritative reconcilers

**Dimension:** Control-Plane Separation  
**Applies to:** `control-plane-implementation`, `bootstrap`  
**Violation:** `WARNING`  
**Experimental:** yes  
**Scoring:** no

Warn when deterministic evidence suggests two active control paths may reconcile the same external resource or lifecycle domain.

This rule is intentionally non-scoring in V0 because coexistence of Crossplane, Terraform/TFE, cloud-native tooling, or migration machinery does not prove co-management by itself. A finding must include the evidence that created the ownership ambiguity.

## Status semantics

- `PASS`: applicable rule has positive deterministic evidence.
- `WARNING`: applicable non-blocking control is unsatisfied or an architectural risk needs human review.
- `FAIL`: applicable non-negotiable boundary is deterministically violated.
- `NOT_APPLICABLE`: required capability/context is absent or cannot be paired; excluded from scoring.

## Conclusion semantics

For a future GitHub Check:

- any scoring `FAIL` -> `failure`;
- no `FAIL`, one or more `WARNING` -> `neutral`;
- all applicable scoring rules `PASS` -> `success`;
- no applicable scoring rules -> `success` with `No IaaP-relevant controls applicable`;
- experimental rules never alter the conclusion in V0.
