# IaaP Guard V0 Fixtures

These fixtures define architecture behavior before the scanner implementation exists.

They are product contract examples, not customer-specific templates.

## Positive fixtures

Positive fixtures prove that IaaP Guard is context-aware and does not fail merely because implementation technologies or denied authority tokens are present.

- `good/product-contract.yaml` — narrow product contract with accountable ownership.
- `good/providerconfig-behind-implementation.yaml` — ProviderConfig exists behind a Crossplane Composition and is not consumer-selectable.
- `good/ai-denylist.json` — dangerous tools appear only in a deny-list; human approval and proposal-only authority remain intact.

## Negative fixtures

- `negative/consumer-terraform-workspace.yaml` -> `IAP-P001 FAIL`
- `negative/consumer-providerconfig.yaml` -> `IAP-P001 FAIL`
- `negative/experience-direct-provision.yaml` -> `IAP-X001 FAIL`
- `negative/ai-apply-authority.json` -> `IAP-A001 FAIL`
- `negative/consumer-lifecycle-policy.yaml` -> `IAP-P002 FAIL`
- `negative/missing-owner.yaml` -> `IAP-P004 WARNING`
- `negative/reconciler-conflict.yaml` -> `IAP-CX01 WARNING` (experimental, non-scoring)
- `negative/missing-approval.json` -> `IAP-A002 FAIL`
- `negative/missing-evidence.yaml` -> `IAP-E001 WARNING`
- `negative/storefront-domain-broader.yaml` -> `IAP-C001 FAIL`

`expected-results.yaml` is the machine-readable acceptance contract for the fixture set.

## Important constraint

A fixture containing a forbidden token does not make the token globally forbidden. The expected result depends on the fixture's component context and structure.
