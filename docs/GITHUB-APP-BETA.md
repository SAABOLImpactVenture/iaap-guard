# IaaP Guard GitHub App — Public Installable Beta

## Purpose

The public GitHub App wraps the proven deterministic IaaP Guard core with a small, stateless GitHub-native runtime.

For IaaP-relevant pull requests, the App now evaluates both the immutable PR-head state and the immutable PR-base state so the existing `IaaP Guard / Architecture` Check can show point-in-time architecture results **and** Evidence Continuity.

```text
GitHub pull request
      ↓ webhook
Public GitHub App
      ↓ signature verified
AWS Lambda Function URL
      ↓ GitHub App JWT
Repository-scoped installation token
      ↓
PR file relevance check
      ↓
      ├── immutable PR-head snapshot ──→ scan-result/v1 ──┐
      └── immutable PR-base snapshot ──→ scan-result/v1 ──┤
                                                         ↓
                                              evidence-manifest/v1
                                                         ↓
                                                  continuity/v1
                                                         ↓
                                      IaaP Guard / Architecture Check
```

The adapter does not redefine classification, rule semantics, scoring, materiality, or continuity semantics.

## Why AWS Lambda + Function URL for the beta

The deterministic core is already Python. A Lambda Function URL provides a small stateless HTTPS runtime without introducing a database, queue, dashboard, container platform, or second implementation language.

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
- **User authorization / OAuth callback:** not required for the current beta.
- **Installation scope:** Any account for the public beta.
- **Marketplace listing:** not required and remains out of scope.

Generate a GitHub App private key after registration. Store the PEM in AWS Secrets Manager. Never commit the PEM or webhook secret.

## Runtime credentials

The deployed runtime uses three App values:

- `IAAP_GUARD_GITHUB_APP_ID` — the non-secret numeric GitHub App ID used as the JWT `iss` claim;
- `IAAP_GUARD_GITHUB_PRIVATE_KEY_SECRET_ARN` — Secrets Manager ARN containing the raw PEM private key;
- `IAAP_GUARD_GITHUB_WEBHOOK_SECRET_ARN` — Secrets Manager ARN containing the raw webhook secret.

The GitHub App **Client ID is not the JWT issuer** used by this runtime. The deployment requires the numeric App ID explicitly.

For local unit testing only, direct `IAAP_GUARD_GITHUB_PRIVATE_KEY` and `IAAP_GUARD_GITHUB_WEBHOOK_SECRET` environment variables are supported. Do not use direct secret environment variables for the deployed beta.

The Lambda execution role can only call `secretsmanager:GetSecretValue` against the two configured secret ARNs.

## Authentication flow

For each handled delivery:

1. Load only the webhook signing secret and verify `X-Hub-Signature-256` using constant-time HMAC comparison.
2. Reject an invalid webhook before loading the GitHub App private key or App ID.
3. Load the numeric GitHub App ID and private key and generate a short-lived RS256 GitHub App JWT.
4. Exchange the App JWT for an installation access token.
5. Scope that installation token to **only the triggering repository** and to:
   - Contents: read;
   - Pull requests: read;
   - Checks: write.
6. Never assume a fixed installation-token length or format.
7. Discard the token after the invocation.

No personal access token is used.

## Pull-request evaluation

The runtime first reads the PR file list.

If no changed file uses a supported analysis suffix, Guard publishes a successful `IaaP Guard / Architecture` Check with an explicit no-relevant-changes result and does not perform the full repository continuity path.

When relevant files changed, the runtime evaluates the complete immutable repository state rather than isolated changed files because architecture rules may require relationships across product contracts, experience definitions, implementation, policy, and evidence.

### Current state

The runtime downloads the triggering repository at the exact PR-head SHA, safely extracts the archive, and invokes the deterministic `scan_path` core.

### Trusted technical baseline

The runtime resolves the PR-base SHA from GitHub pull-request state and evaluates that exact immutable repository revision using the same deterministic core.

The proposed change cannot nominate or replace its own continuity baseline.

For a Check `rerequested` event, the runtime resolves the current pull request before establishing the base/head pair so the rerequest uses GitHub's current PR state rather than trusting stale user-supplied baseline metadata.

The scanner still does not execute repository code.

## Evidence Continuity

The base and head `scan-result/v1` records are compared through the deterministic Evidence Continuity model.

The GitHub Check can show:

- **SUPPORTED** — no Guard-material rule/finding change was detected;
- **REVIEW REQUIRED** — a Guard-material change means prior evidence should be revalidated;
- **NOT ESTABLISHED** — continuity could not be established from an appropriate baseline.

The output can include:

- base and head immutable revisions;
- Guard/ruleset/scoring versions;
- materiality;
- bounded disposition;
- rule-state transition count;
- introduced/resolved finding-evidence deltas; and
- deterministic evidence digest.

### Authority boundary

Evidence Continuity is **advisory** in the current App contract.

The deterministic repository scan continues to own the GitHub Check conclusion:

| Deterministic core result | GitHub Check conclusion |
|---|---|
| PASS / no applicable failures | `success` |
| WARNING | `neutral` |
| FAIL | `failure` |
| No relevant changed files | `success` |

A continuity result of `review_required` does not silently convert an otherwise successful repository scan into a new blocking failure. It signals that accountable revalidation is needed under the organization's actual governance process.

**Evidence continuity is not authorization continuity.** The App does not determine legal, institutional, security, compliance, exception, risk-acceptance, deployment, or disposition authority.

See `docs/EVIDENCE-CONTINUITY.md` and `docs/PR-BASE-EVIDENCE-CONTINUITY.md` for the detailed contracts.

## Check semantics

The Check output includes repository identity, exact head SHA, rule catalog version, scoring version, score, finding count, rule IDs, paths, deterministic evidence, and recommendations.

For relevant PRs, the Check also includes the bounded Evidence Continuity section described above.

`external_id` is derived from PR number + immutable head SHA. Repeated delivery for the same revision updates the existing Guard Check rather than intentionally creating contradictory duplicates.

A manual GitHub Check re-request re-evaluates the current PR through the same deterministic path.

## Product-aware enrichment

If trusted multi-repository product scope is available, the product-aware runtime may append product assessment and planning context to the same Check.

That enrichment must preserve the repository Evidence Continuity section. Product-level context remains advisory and cannot silently replace the triggering repository's Check conclusion semantics.

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

Deploy using your chosen stack/region and pass the three parameters:

```bash
sam deploy --guided \
  --parameter-overrides \
    GitHubAppId=<numeric-app-id> \
    GitHubPrivateKeySecretArn=<private-key-secret-arn> \
    GitHubWebhookSecretArn=<webhook-secret-arn>
```

After deployment, copy the `WebhookUrl` stack output into the GitHub App's Webhook URL field.

The endpoint also supports a simple `GET` health response. GitHub webhook processing requires `POST` with a valid signature.

## Beta limits and explicit exclusions

The current beta does not add:

- a persistent customer database;
- customer cloud, Kubernetes, Terraform/TFE, or AI credentials;
- provisioning or reconciliation;
- repository edits;
- pull-request creation or merge authority;
- auto-remediation;
- autonomous exception/risk disposition;
- legal or compliance authorization claims;
- a SaaS dashboard;
- organization analytics;
- Marketplace or billing;
- FedRAMP/ATO claims;
- production-readiness claims.

The purpose is to prove useful GitHub-native architecture evidence, trusted base/head continuity, and accountable review signals before investing in broader hosted-system complexity.
