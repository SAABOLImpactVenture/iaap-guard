# Phase 17 Validation

## Status

**COMPLETE — independent external-adoption evidence, finding adjudication, V1 contract
freeze, and protected validation are complete.**

## Campaign

The read-only external-adoption campaign ran from `main` commit
`24638ca86089b4d1371a3de90b3aead858cd22e8` through manual GitHub Actions run
[`31912538972`](https://github.com/SAABOLImpactVenture/iaap-guard/actions/runs/31912538972).

The deterministic runner checked out three independently maintained public Terraform
module repositories at immutable 40-character commit SHAs:

| Ecosystem | Repository | Revision | Result |
|---|---|---|---|
| AWS | `terraform-aws-modules/terraform-aws-vpc` | `0a36bd54069c64be2da788b2afb5df0a8e8e7398` | WARNING, 17 |
| Azure | `Azure/terraform-azurerm-avm-ptn-alz-connectivity-hub-and-spoke-vnet` | `c8c984f60c61981b2cc4039471537de4995961b9` | WARNING, 17 |
| Google Cloud | `terraform-google-modules/terraform-google-network` | `66532db28ab7aabfb0d8d31cb0534788a78e3221` | WARNING, 17 |

The workflow used only `contents: read`, did not install the GitHub App in any target,
and did not create branches, checks, issues, pull requests, secrets, webhooks, or changes
in adopter repositories.

## Finding adjudication

Each repository produced the same three non-blocking findings:

- `IAP-P003`: infrastructure implementation without a recognizable consumer product
  contract;
- `IAP-G001`: no independently executable deterministic product-boundary validation;
  and
- `IAP-E001`: no machine-observable lifecycle evidence path.

All nine findings are **context-dependent**. The targets are standalone Terraform modules,
not repositories claiming to be complete Infrastructure-as-a-Product products. The
warnings accurately describe the product-layer evidence absent from the analyzed scope,
but they must not be read as generic Terraform-quality defects or instructions that every
module must become a complete product.

No finding was adjudicated as a false positive, no material rule-quality defect was found,
and no rule change or authority expansion was required. Neutral conclusions correctly
preserved this distinction.

## Retained evidence

The exact workflow output is retained at
`artifacts/phase-17/external-adoption.json`. Its SHA-256 digest is
`7efb6848e97762b799e2ea74ff961372be7572fc135f965d3507dff16c43109d`.

The machine-readable adjudication is retained at
`artifacts/phase-17/adjudication.json`. The source workflow artifact
`phase-17-external-adoption-31912538972` has artifact ID `9254059310` and digest
`sha256:d1389433dfa0f04cf5367123ffd1fc84211c6419b422ee053d8331d6d5e94908`.

## V1 contract freeze

The V1 rule, schema, scoring, planning, and authority contracts are frozen in
[`V1-CONTRACT-FREEZE.md`](V1-CONTRACT-FREEZE.md). Backward-incompatible changes require
an explicitly versioned successor contract; the freeze does not grant new product or
infrastructure authority.

## Boundary confirmation

Phase 17 validated rule usefulness against unfamiliar repositories. It did not turn Guard
into a generic IaC scanner, install or operate in adopter accounts, modify adopter
repositories, ingest organizational OKRs, manage work, execute infrastructure, or make
authorization decisions.
