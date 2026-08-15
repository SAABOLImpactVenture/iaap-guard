# AWS OIDC Deployment

IaaP Guard's beta deployment can be operated from GitHub Actions without storing long-lived AWS access keys in GitHub.

## Security model

The deployment workflow requests a short-lived GitHub OIDC token and assumes the dedicated AWS role `IaaPGuardDeploymentRole` in account `070096877875`. The AWS trust relationship is limited to this repository's immutable GitHub owner/repository IDs and the `main` branch.

The workflow grants only:

- `contents: read` to read the repository; and
- `id-token: write` to request the GitHub OIDC token.

The GitHub App runtime permissions are unchanged. This workflow does not expand IaaP Guard's App installation permissions, customer-data access, provisioning authority, remediation authority, merge authority, or deployment authority inside customer repositories.

## Manual operations

The workflow `.github/workflows/deploy-aws-beta.yml` is intentionally `workflow_dispatch` only and supports three operations.

### `identity`

Authenticates through GitHub OIDC and verifies the assumed AWS identity plus the current `iaap-guard-beta` stack state. It does not build, upload, create a change set, or modify AWS resources.

### `plan`

Builds the current `main` revision with AWS SAM and creates a non-executing CloudFormation change set for the existing `iaap-guard-beta` stack. The workflow summary records:

- the exact Git commit SHA;
- the generated CloudFormation change-set ARN; and
- the resource-level CloudFormation change summary.

`plan` does not execute the change set.

### `deploy`

Executes only a caller-supplied CloudFormation change-set ARN. To reduce accidental execution, the caller must provide all three values:

1. `expected_sha` equal to the exact selected `main` commit;
2. `change_set_arn` copied from the successful `plan` run; and
3. `confirm` equal to `DEPLOY`.

Before execution, the workflow verifies that the change set belongs to the expected AWS account, region, and `iaap-guard-beta` stack and that CloudFormation reports it as `CREATE_COMPLETE` / `AVAILABLE`.

## Current beta deployment parameters

The workflow preserves the existing beta stack settings:

- Region: `us-east-2`
- Stack: `iaap-guard-beta`
- GitHub App ID: `4529329`
- Reserved concurrency value: `5`
- Reserved concurrency application: disabled (`GuardReservedConcurrencyEnabled=false`)
- GitHub App private key: existing Secrets Manager ARN
- GitHub webhook secret: existing Secrets Manager ARN

Secret *values* are never committed to the repository or retrieved by the deployment workflow.

## Phase 15 sequence

For Phase 15 live acceptance:

1. run `identity` to prove OIDC assumption;
2. run `plan` from the Phase 15 `main` revision;
3. review the generated change set;
4. run `deploy` with the exact plan SHA and change-set ARN;
5. verify the deployed stack is healthy; and
6. perform the separately staged READY -> BLOCKED -> READY live acceptance campaign.

Phase 15 is complete; deployment and retained live acceptance evidence are documented in [`PHASE-15-VALIDATION.md`](PHASE-15-VALIDATION.md) and [`planning/phase-15.md`](../planning/phase-15.md).

## Root account boundary

The AWS account root identity was used only to bootstrap the GitHub OIDC provider and deployment-role trust. Routine deployment must use the OIDC deployment role rather than the root identity.
