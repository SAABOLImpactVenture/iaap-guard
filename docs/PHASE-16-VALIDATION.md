# Phase 16 Validation

## Status

**IN PROGRESS — deployed beta operational verification is complete; remaining Phase 16
closure key results are still pending.**

## Operational verification

The existing `iaap-guard-beta` AWS stack was verified from `main` commit
`1245f66acfb10ff3bfb1ec72c4762ff080a1f865` through the manual GitHub Actions OIDC
workflow.

Verification run [`31995153385`](https://github.com/SAABOLImpactVenture/iaap-guard/actions/runs/31995153385)
completed successfully on `2026-08-15T16:18:39Z`.

The read-only verification confirmed:

- GitHub OIDC assumed the expected beta deployment role;
- the CloudFormation stack was in a stable complete state;
- deployed parameters matched the approved GitHub App and concurrency contract;
- secret configuration used distinct Secrets Manager ARN references without retrieving
  or exposing secret values;
- the HTTPS webhook output was present;
- the expected Lambda function, log group, and CloudWatch alarms were deployed;
- log retention and alarm definitions matched the beta operational contract; and
- the public health endpoint returned the exact expected service and status contract.

The `verify` operation did not build, create a change set, deploy, mutate the stack, or
retrieve secret values.

## Permission correction

The initial verification failed closed because the effective deployment-role policy did
not allow `cloudformation:DescribeStackResources`. The IAM policy simulator reproduced
the implicit deny.

A separate read-only statement was added to the existing `IaaPGuardBetaDeployment`
inline policy. It allows only `cloudformation:DescribeStackResources` and is scoped to
the `iaap-guard-beta` CloudFormation stack. The successful verification run above was
performed after that correction.

## Retained evidence

The GitHub Actions run and job summary retain the authoritative operational evidence,
including the exact `main` revision, execution time, verification result, and individual
contract checks.

No AWS credentials, secret values, infrastructure mutations, or expanded product
authority are part of this evidence.

## Boundary confirmation

This verification establishes beta operability only. It does not give IaaP Guard
infrastructure provisioning, remediation, deployment, exception, compliance,
risk-acceptance, pull-request, or merge authority.

Phase 16 remains open until its remaining security, reproducibility, documentation,
final closure-record, and complete validation key results are satisfied.
