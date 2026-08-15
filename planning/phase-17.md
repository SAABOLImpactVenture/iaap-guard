# Phase 17 — External Adoption Validation

## Status

**IN PROGRESS**

## Objective

Validate IaaP Guard's usefulness and rule quality against independent, unfamiliar
infrastructure repositories without installing the GitHub App, modifying adopter
repositories, or treating generic IaC quality as Infrastructure-as-a-Product evidence.

## Campaign protocol

The campaign uses public repositories as read-only fixtures. Every repository and result
is pinned to an immutable 40-character commit SHA. No repository receives a webhook,
Check, branch, issue, pull request, secret, or configuration change.

The initial cohort spans independently maintained AWS, Azure, and Google Cloud Terraform
modules. Selection is based on public availability, manageable archive size, active or
representative infrastructure content, and no dependency on SAABOL repositories.

## Key results

- [ ] A deterministic external-adoption runner and machine-readable campaign manifest
  are implemented and tested.
- [ ] At least three independent infrastructure repositories across three cloud
  ecosystems are scanned at immutable revisions.
- [ ] Every finding is adjudicated as useful, context-dependent, false positive, or
  outside Guard's V1 product contract.
- [ ] Material rule-quality defects are corrected without broadening Guard into generic
  IaC scanning, compliance, work management, or infrastructure execution.
- [ ] V1 rule, schema, scoring, planning, and authority contracts are frozen.
- [ ] A retained Phase 17 validation record and reproducible evidence artifact are
  merged after the complete deterministic suite and protected checks pass.

## Exit condition

Phase 17 is complete when the independent campaign is reproducible, its findings are
adjudicated, material defects are resolved, the V1 contracts are frozen, and the retained
evidence passes the protected pull-request path.
