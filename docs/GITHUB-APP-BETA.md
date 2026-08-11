# IaaP Guard GitHub App — Phase 10 Public Installable Beta

## Purpose

Phase 10 wraps the proven deterministic IaaP Guard core with the smallest publicly installable GitHub-native runtime.

```text
GitHub pull request
      ↓ webhook
Public GitHub App
      ↓ signature verified
AWS Lambda Function URL
      ↓ GitHub App JWT
Repository-scoped installation token
      ↓ read PR files + immutable head snapshot
Deterministic IaaP Guard core
      ↓ scan-result/v1
IaaP Guard / Architecture Check Run
```

The adapter does not redefine classification, rule semantics, scoring, or conclusions.

## Why AWS Lambda + Function URL for the beta

The deterministic core is already Python. A Lambda Function URL therefore provides a small stateless HTTPS runtime without introducing a database, queue, dashboard, container platform, or second implementation language.

The Function URL uses `AuthType: NONE` because GitHub must reach it over public HTTPS. Authenticity is enforced at the application boundary by validating GitHub's `X-Hub-Signature-256` HMAC before payload processing.

This is a beta hosting decision, not a permanent product dependency. The GitHub App adapter remains separable from the deterministic core.

## GitHub App registration contract

Create the App under the `SAABOLImpactVenture` organization and configure it to be installable by **Any account**.

Use `config/github-app-v0.json` as the machine-readable authority contract.

### Repository permissions

| Permission | Access |
|---|---|
| Metadata | Read |
| Contents | Read |
| Pull requests | Read |
| Checks | Read and write |

Do not grant Actions, Administration, Deployments, Issues, Members, Secrets, Workflows, Contents write, Pull requests write, or organization-management permissions.

### Events

Subscribe only to:

- **Pull request** — the runtime processes `opened`, `synchronize`, `reopened`, and `ready_for_review` and ignores other actions;
- **Check run** — the runtime processes only `rerequested` for `IaaP Guard / Architecture` checks created by this adapter.

GitHub App event subscriptions are event-level; action filtering is enforced deterministically by the runtime.

### Other App settings

- **Webhook:** Active.
- **Webhook URL:** the `WebhookUrl` output from the Lambda deployment.
- **Webhook secret:** a cryptographically random value stored in AWS Secrets Manager and entered into the GitHub App settings.
- **User authorization / OAuth callback:** not required for V0.
- **Installation scope:** Any account for the public beta.
- **Marketplace listing:** not required and remains out of scope.

Generate a GitHub App private key after registration. Store the PEM in AWS Secrets Manager. Never commit the PEM or webhook secret.

## Runtime credentials

The deployed runtime uses three App values:

- `IAAP_GUARD_GITHUB_APP_ID` — the non-secret numeric GitHub App ID used as the JWT `iss` claim;
- `IAAP_GUARD_GITHUB_PRIVATE_KEY_SECRET_ARN` — Secrets Manager ARN containing the raw PEM private key;
- `IAAP_GUARD_GITHUB_WEBHOOK_SECRET_ARN` — Secrets Manager ARN containing the raw webhook secret.

The GitHub App **Client ID is not the JWT issuer used by this beta runtime**. Live Phase 10 installation testing against the GitHub REST API version pinned by the adapter returned HTTP 401 when a string Client ID was used: `Issuer claim (iss) must be an Integer`. The deployment therefore requires the numeric App ID explicitly.

For local unit testing only, direct `IAAP_GUARD_GITHUB_PRIVATE_KEY` and `IAAP_GUARD_GITHUB_WEBHOOK_SECRET` environment variables are supported. Do not use direct secret environment variables for the deployed beta.

The Lambda execution role can only call `secretsmanager:GetSecretValue` against the two configured secret ARNs.

## Beta operational guardrails

The Lambda reserves a conservative default concurrency of **5** through the `GuardReservedConcurrency` deployment parameter. This bounds simultaneous beta executions without changing the stateless webhook architecture. In an emergency, an operator can update the stack with reserved concurrency set to **0** to stop Lambda invocations. While set to zero, health checks and GitHub webhook deliveries will be throttled; restore a positive limit deliberately after the issue is resolved.

The stack explicitly manages the function's CloudWatch Logs log group with **14-day retention**. It also creates CloudWatch alarms for any Lambda Errors, any Lambda Throttles, and maximum Duration at or above **50 seconds** against the 60-second function timeout. Missing metric data is treated as not breaching. The alarms intentionally have no notification actions in this phase; notification routing remains a later operational decision.

## Authentication flow

For each handled delivery:

1. Load only the webhook signing secret and verify `X-Hub-Signature-256` using constant-time HMAC comparison.
2. Reject an invalid webhook before loading the GitHub App private key or App ID.
3. Load the numeric GitHub App ID and private key and generate a short-lived RS256 GitHub App JWT.
4. Exchange the App JWT for an installation access token.
5. Scope that installation token to **only the repository that triggered the webhook** and to:
   - Contents: read;
   - Pull requests: read;
   - Checks: write.
6. Never assume a fixed installation-token length or format.
7. Discard the token after the invocation.

No personal access token is used.

## Pull-request evaluation

The runtime first reads the PR file list.

If no changed file uses a V0-supported analysis suffix, Guard publishes a successful `IaaP Guard / Architecture` Check with an explicit no-relevant-changes result and does not download the repository snapshot.

When relevant files changed, the runtime downloads the repository at the exact PR head SHA, safely extracts the immutable snapshot, and invokes the existing `scan_path` core against the complete head state. The complete snapshot is used rather than isolated changed files because architecture rules may require relationships across product contracts, experience definitions, implementation, policy, and evidence.

The scanner still does not execute repository code.

## Check semantics

| Deterministic core result | GitHub Check conclusion |
|---|---|
| PASS / no applicable failures | `success` |
| WARNING | `neutral` |
| FAIL | `failure` |
| No relevant changed files | `success` |

The Check output includes repository identity, exact head SHA, rule catalog version, scoring version, score, finding count, rule IDs, paths, deterministic evidence, and recommendations.

`external_id` is derived from PR number + immutable head SHA. Repeated delivery for the same revision updates the existing Guard Check rather than intentionally creating contradictory duplicates.

A manual GitHub Check re-request re-evaluates the same PR/head identity through the same deterministic path.

## Repository snapshot safety

The beta places explicit bounds around untrusted repository archives:

- compressed archive maximum: 25 MB;
- archive member maximum: 20,000;
- extracted regular-file bytes maximum: 100 MB;
- absolute paths and `..` traversal are rejected;
- symbolic links, hard links, devices, and FIFOs are rejected;
- cross-host archive redirects do not retain the GitHub Authorization header.

These are beta product limits, not claims of enterprise-scale repository support.

## Deploy

Prerequisites:

- an AWS account/role permitted to deploy the SAM stack;
- AWS SAM CLI;
- the numeric GitHub App ID from the App General settings page;
- one Secrets Manager secret containing the raw GitHub App PEM private key;
- one Secrets Manager secret containing the raw webhook secret.

Build from the repository root:

```bash
sam build --template-file deploy/aws-lambda/template.yaml
```

Deploy using your chosen stack/region, pass the three required GitHub App parameters, and optionally override the default beta concurrency:

```bash
sam deploy --guided \
  --parameter-overrides \
    GitHubAppId=<numeric-app-id> \
    GitHubPrivateKeySecretArn=<private-key-secret-arn> \
    GitHubWebhookSecretArn=<webhook-secret-arn> \
    GuardReservedConcurrency=5
```

After deployment, copy the `WebhookUrl` stack output into the GitHub App's Webhook URL field.

The endpoint also supports a simple `GET` health response. GitHub webhook processing requires `POST` with a valid signature.

## Beta limits and explicit exclusions

This phase does not add:

- a persistent database;
- customer cloud, Kubernetes, Terraform/TFE, or AI credentials;
- provisioning or reconciliation;
- repository edits;
- pull-request creation or merge authority;
- auto-remediation;
- a SaaS dashboard;
- organization analytics;
- Marketplace or billing;
- FedRAMP/ATO claims;
- production-readiness claims.

The purpose is to prove public/private GitHub installation and correct PR value delivery before investing in any of those capabilities.
