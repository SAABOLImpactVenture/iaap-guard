# Phase 16 Validation

## Status

**COMPLETE — public-beta closure evidence, controls, reproducibility, boundaries, and
protected validation are complete.**

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

## Security control review

The Phase 16 security-control review was completed against `main` commit
`4a6ad20` on `2026-08-15`.

### Dependency controls

Dependabot high-severity alert
[`#1`](https://github.com/SAABOLImpactVenture/iaap-guard/security/dependabot/1)
was resolved by pull request
[`#41`](https://github.com/SAABOLImpactVenture/iaap-guard/pull/41), which upgraded
`cryptography` from `49.0.0` to patched release `50.0.0`.

The declared application and CI dependency sets installed successfully in a clean
Python 3.12 virtual environment, `pip check` reported no broken requirements, and all
85 deterministic tests passed.

### GitHub Actions controls

Repository Actions settings allow only selected actions and reusable workflows.
GitHub-owned actions are allowed, Marketplace actions are not broadly trusted, and the
third-party allowlist is limited to:

- `aws-actions/configure-aws-credentials@*`;
- `aws-actions/setup-sam@*`; and
- `devcontainers/ci@*`.

Full-length commit SHA pinning is enforced. Every external action reference in the
repository is pinned to a full commit SHA. Workflows declare explicit permissions;
ordinary validation workflows use `contents: read`, and only the AWS OIDC workflow adds
the required `id-token: write`.

The default workflow token is read-only for repository contents and packages. GitHub
Actions cannot create or approve pull requests.

### GitHub App controls

The live IaaP Guard GitHub App matches the tested least-privilege contract:

- Checks: read and write;
- Contents: read-only;
- Pull requests: read-only;
- Metadata: mandatory read-only;
- all other repository, organization, account, and enterprise permissions: no access;
  and
- subscribed events: only Check run and Pull request.

### Protected branch controls

The `main` branch requires the pull-request path, dismisses stale approvals, requires an
up-to-date branch, and requires `validate-core`, `dogfood-action`,
`dependency-review`, and `CodeQL`. Conversations must be resolved, administrators cannot
bypass the rule, and force pushes and branch deletion are disabled.

The required approving-review count remains zero for the single-maintainer public beta;
this does not bypass the required pull-request path or required checks.

## Clean-adopter validation

A clean-adopter campaign was completed on `2026-08-15` using the temporary public
repository
[`SAABOLImpactVenture/iaap-guard-adopter-validation`](https://github.com/SAABOLImpactVenture/iaap-guard-adopter-validation).
The repository was created without Guard-specific configuration and received only a
minimal Terraform change on pull request
[`#1`](https://github.com/SAABOLImpactVenture/iaap-guard-adopter-validation/pull/1)
at revision `7bb6f811a7001233aaed861351eaf755df91b902`.

### Installation and live result

The repository was added explicitly to the existing selected-repository IaaP Guard
installation. Closing and reopening the pull request emitted an eligible
`pull_request.reopened` webhook. GitHub recorded the delivery, the Check creation, and
the completed Check.

The
[`IaaP Guard / Architecture` Check](https://github.com/SAABOLImpactVenture/iaap-guard-adopter-validation/pull/1/checks?check_run_id=95076939126)
completed in two seconds with a neutral `WARNING` conclusion, score `0`, and three
expected findings for the intentionally incomplete Terraform-only fixture:

- `IAP-P003` — no recognizable consumer product contract;
- `IAP-G001` — no independently executable deterministic product-boundary validation;
  and
- `IAP-E001` — no machine-observable lifecycle evidence path.

The Check rendered a deterministic improvement plan with three objectives, six key
results, three epics, three features, three candidate stories, and twelve candidate
tasks. Evidence Continuity correctly rendered `REVIEW REQUIRED` against the PR base
without changing authorization or merge authority.

### Troubleshooting and cleanup

The campaign reproduced the most important first-installation diagnostic: selecting a
repository in the installation picker does not grant access until the separate
installation `Save` action succeeds. Before that save, GitHub sent no webhook and the
pull request showed no Guard Check. After the saved installation contained four
repositories, the next eligible event produced the Check normally.

No adopter AWS credentials, cloud credentials, workflow installation, repository
secrets, Guard configuration, or write authority were required. After validation:

- pull request `#1` was closed;
- the temporary repository was removed from the App installation;
- the installation returned to its original three repositories; and
- the validation repository was archived read-only rather than deleted, retaining the
  public evidence and allowing reversible recovery.

This campaign validates installation, first-result interpretation, troubleshooting,
removal, and operator cleanup from a clean adopter perspective.

## V1 boundary consistency review

The Phase 16 V1 boundary review was completed against `main` commit
`0d28efacd03c88746afb5fb355329727a1c1bd91` on `2026-08-15`.

`docs/PRODUCT.md#explicit-exclusions` is now the canonical V1 boundary. README,
architecture, adoption-readiness, adopter-prerequisite, security, and GitHub App
documentation explicitly inherit that boundary rather than defining independent scope.

The review confirmed consistent public-beta limits:

- at most 12 registered repositories per logical product;
- same-owner and same-visibility automatic V1 federation;
- a 20 MB cross-repository relationship bundle;
- 25 MB compressed repository archives;
- 20,000 archive members;
- 100 MB extracted regular-file bytes;
- 1 MB per analyzed file; and
- supported full-scan suffixes limited to `.yaml`, `.yml`, `.json`, `.tf`,
  `.tofu`, `.hcl`, `.md`, `.py`, and `.sh`.

The documents consistently exclude organizational OKR ingestion, enterprise strategy
and work management, infrastructure execution, customer infrastructure credentials,
repository mutation, automated authorization or remediation, persistent customer
analytics, automatic cross-organization V1 federation, Marketplace billing, compliance
claims, and production-readiness claims.

## Final closure candidate

The Phase 16 closure candidate is based on `main` commit
`d520b905721dd0f35118bd67b1e93a54ee218e39` on `2026-08-15`.

The retained Phase 16 record now covers deployed operational verification, the
least-privilege security and dependency review, a reversible clean-adopter campaign,
and a cross-document V1 boundary review. The complete deterministic suite previously
passed all 85 tests, and protected pull requests through boundary-consistency PR
[#44](https://github.com/SAABOLImpactVenture/iaap-guard/pull/44) completed the required
validation, dogfood, dependency-review, and CodeQL checks.

The first protected check run for closure PR
[#45](https://github.com/SAABOLImpactVenture/iaap-guard/pull/45) completed successfully:
the deterministic validation and dogfood jobs, Dependency Review, and CodeQL all passed.
This completion declaration is therefore carried on a fresh PR head and must pass those
same protected checks once more before merge.

## Boundary confirmation

This verification establishes beta operability only. It does not give IaaP Guard
infrastructure provisioning, remediation, deployment, exception, compliance,
risk-acceptance, pull-request, or merge authority.

Phase 16 is complete. Phase 17 may validate independent adoption and rule quality
without reopening the frozen V1 authority boundary.
