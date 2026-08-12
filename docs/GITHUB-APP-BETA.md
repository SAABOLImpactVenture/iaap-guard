# IaaP Guard GitHub App — Public Installable Beta

## Purpose

The public GitHub App wraps the proven deterministic IaaP Guard core with a small, stateless GitHub-native runtime.

For IaaP-relevant pull requests, the App can now provide three distinct layers of evidence in the existing `IaaP Guard / Architecture` Check:

1. repository architecture evaluation;
2. PR-base Evidence Continuity; and
3. trusted multi-repository Product Assessment and Product Improvement Plan when reciprocal product scope is configured.

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
                           optional trusted multi-repository federation
                                                         ↓
                                      IaaP Guard / Architecture Check
```

The adapter does not redefine classification, rule semantics, scoring, product relationship semantics, materiality, or continuity semantics.

## Before installing: adopter prerequisites

Repository teams should read [`ADOPTION-PREREQUISITES.md`](ADOPTION-PREREQUISITES.md) before the first live PR.

That guide covers:

- supported file types;
- repository/archive limits;
- what causes a full scan versus `No relevant changes`;
- Evidence Continuity prerequisites;
- multiple-repository enrollment;
- reciprocal `.iaap/product.yaml` requirements;
- same-owner and same-visibility federation boundaries;
- App access to required member repositories;
- `INCOMPLETE` causes;
- the 12-repository V1 limit; and
- common troubleshooting paths.

The deployment prerequisites later in this document are for the **App operator**. Most repository users should not need AWS credentials or access to the hosting stack.

## Why AWS Lambda + Function URL for the beta

The deterministic core is already Python. A Lambda Function URL provides a small stateless HTTPS runtime without introducing a database, queue, dashboard, container platform, or second implementation language.

The Function URL uses `AuthType: NONE` because GitHub must reach it over public HTTPS. Authenticity is enforced at the application boundary by validating GitHub's `X-Hub-Signature-256` HMAC before payload processing.

This is a beta hosting decision, not a permanent product dependency. The GitHub App adapter remains separable from the deterministic core.

## GitHub App registration contract

Create the App under the owning organization and configure it to be installable by the intended accounts. The SAABOL public-beta reference registration is under `SAABOLImpactVenture` and uses **Any account** installation scope.

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

## Beta operational guardrails

The Lambda reserves a conservative default concurrency of **5** through the `GuardReservedConcurrency` deployment parameter. This bounds simultaneous beta executions without changing the stateless webhook architecture. In an emergency, an operator can update the stack with reserved concurrency set to **0** to stop Lambda invocations. While set to zero, health checks and GitHub webhook deliveries will be throttled; restore a positive limit deliberately after the issue is resolved.

Some low-quota or new AWS accounts cannot allocate the default reserved concurrency. For those accounts, set `GuardReservedConcurrencyEnabled=false` temporarily. This omits the function-level reserved concurrency setting; it does not set concurrency to zero. Invocations remain bounded by the regional Lambda account concurrency quota, but disabling reserved concurrency does **not** provide equivalent per-function isolation. As the beta matures, increasing the regional Lambda concurrency quota and re-enabling the per-function limit is preferred.

The stack explicitly manages the function's CloudWatch Logs log group with **14-day retention**. It also creates CloudWatch alarms for any Lambda Errors, any Lambda Throttles, and maximum Duration at or above **50 seconds** against the 60-second function timeout. Missing metric data is treated as not breaching. The alarms intentionally have no notification actions in this phase; notification routing remains a later operational decision.

## Authentication flow

For each handled delivery:

1. Load only the webhook signing secret and verify `X-Hub-Signature-256` using constant-time HMAC comparison.
2. Reject an invalid webhook before loading the GitHub App private key or App ID.
3. Load the numeric GitHub App ID and private key and generate a short-lived RS256 GitHub App JWT.
4. Exchange the App JWT for an installation access token.
5. Scope the triggering-repository token to **only the triggering repository** and to:
   - Contents: read;
   - Pull requests: read;
   - Checks: write.
6. Never assume a fixed installation-token length or format.
7. Discard the token after the invocation.

No personal access token is used.

### Related-repository token boundary

When trusted product scope is enabled, Guard does **not** broaden the triggering token.

For each candidate related repository, it obtains a separate short-lived installation token restricted to that repository and asks only for:

- Contents: read.

That token is used to read the related default-branch product manifest, resolve the immutable default-branch revision, and scan the member snapshot. It is discarded after the stateless invocation.

## Pull-request evaluation

The runtime first reads the PR file list.

If no changed file uses a supported analysis suffix, Guard publishes a successful `IaaP Guard / Architecture` Check with an explicit no-relevant-changes result and does not perform the full repository continuity path.

Supported suffixes are:

```text
.yaml  .yml  .json  .tf  .tofu  .hcl  .md  .py  .sh
```

When relevant files changed, the runtime evaluates the complete immutable repository state rather than isolated changed files because architecture rules may require relationships across product contracts, experience definitions, implementation, policy, and evidence.

### Current state

The runtime downloads the triggering repository at the exact PR-head SHA, safely extracts the archive, and invokes the deterministic `scan_path` core.

### Trusted technical baseline

The runtime resolves the PR-base SHA from GitHub pull-request state and evaluates that exact immutable repository revision using the same deterministic core.

The proposed change cannot nominate or replace its own continuity baseline.

For a Check `rerequested` event, the runtime resolves the current pull request before establishing the base/head pair so the rerequest uses GitHub's current PR state rather than trusting stale user-supplied baseline metadata.

The scanner does not execute repository code.

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

### Live Phase 14 acceptance

Phase 14 is complete. The deployed App produced both required paths on one fresh PR:

- non-Guard-material change → architecture PASS 100 + Evidence Continuity `SUPPORTED`;
- controlled `IAP-P004` material change → architecture WARNING 67 + Evidence Continuity `REVIEW REQUIRED` + `human_review_required` disposition.

The proof also preserved the existing repository Check conclusion semantics.

Canonical evidence: [`Phase 14 live acceptance`](https://github.com/SAABOLImpactVenture/ai-powered-infrastructure-as-a-product/blob/main/artifacts/phase-14/live-acceptance.json).

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

## Product-aware enrichment

### Product Readiness

When trusted registration is present, the App appends `READY`,
`READY_WITH_ADVISORIES`, or `BLOCKED` context with exact member obstacles and next
actions. A blocked required member prevents misleading product-health rendering while
repository architecture and Evidence Continuity remain visible. Readiness never changes
the repository-owned Check conclusion and uses the existing related-repository
`contents:read` token path; no permission type is added.

If the triggering repository carries a trusted default-branch `.iaap/product.yaml`, the product-aware runtime can append a Product Assessment and Product Improvement Plan to the same Check.

### Product membership trust

The triggering PR is not allowed to define or expand live federation by itself.

Guard reads product membership from the triggering repository's default branch and requires every related repository to reciprocally publish the same normalized product identity and membership on its own default branch.

Automatic V1 federation additionally requires:

- the related repository is explicitly registered;
- the triggering repository registers itself;
- the related repository is under the same GitHub owner;
- the related repository has the same visibility;
- the IaaP Guard App installation can access the related repository;
- the related repository has a resolvable default branch; and
- the product contains no more than 12 registered repositories.

A missing required member produces `INCOMPLETE` rather than silent omission.

### Relationship evaluation

Member repositories are scanned independently from immutable snapshots. Guard then builds a separate temporary relationship bundle containing only artifacts classified as `consumer-contract` or `experience`.

The V1 relationship bundle is capped at **20 MB**. If it cannot be completed safely, the Product Assessment becomes `INCOMPLETE` and records `IAP-PR002`.

The initial relationship rule is:

- `IAP-C001` — consumer/storefront constraints must remain compatible with the canonical product contract.

### Live Phase 12 acceptance

Phase 12 is complete. The live proof demonstrated:

- reciprocal default-branch membership across two real repositories;
- 2/2 trusted federation;
- both individual members scoring 100 while the logical product failed at 96 because of an `IAP-C001` cross-repository mismatch;
- a generated product Improvement Plan;
- targeted Backstage remediation; and
- final federated SUCCESS 100 plus a separate primary-member SUCCESS 100 revalidation.

Canonical evidence: [`Phase 12 live federation acceptance`](https://github.com/SAABOLImpactVenture/ai-powered-infrastructure-as-a-product/blob/main/artifacts/phase-12/live-federation-acceptance.json).

### Check authority boundary

Product-aware enrichment must preserve the repository Evidence Continuity section.

The triggering repository result remains authoritative for the GitHub Check conclusion in V1. Product-level context is advisory and cannot silently turn an unrelated member problem into a new blocking merge policy.

A future product-specific blocking Check would require a separate explicit product/governance decision.

## Check semantics

The Check output can include:

- repository identity;
- exact head SHA;
- rule catalog version;
- scoring version;
- repository score and finding count;
- rule IDs, paths, deterministic evidence, and recommendations;
- PR-base Evidence Continuity;
- Product Assessment member evidence, completeness, weakest-member score, relationship status, and product findings; and
- Product Improvement Plan when findings exist.

`external_id` is derived from PR number + immutable head SHA. Repeated delivery for the same revision updates the existing Guard Check rather than intentionally creating contradictory duplicates.

A manual GitHub Check rerequest re-evaluates the current PR through the same deterministic path.

## Repository snapshot safety

The beta places explicit bounds around untrusted repository archives:

- compressed archive maximum: 25 MB;
- archive member maximum: 20,000;
- extracted regular-file bytes maximum: 100 MB;
- individual analyzed file maximum: 1 MB;
- absolute paths and `..` traversal are rejected;
- symbolic links, hard links, devices, and FIFOs are rejected;
- cross-host archive redirects do not retain the GitHub Authorization header.

The scanner ignores common generated/vendor locations including `.git`, `.venv`, `venv`, `node_modules`, `vendor`, `dist`, `build`, `__pycache__`, `artifacts`, and `.work`.

These are beta product limits, not claims of enterprise-scale repository support.

## Deploy — operator path

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
    GuardReservedConcurrencyEnabled=true \
    GuardReservedConcurrency=5
```

For a low-quota account that cannot allocate reserved concurrency, deploy temporarily with `GuardReservedConcurrencyEnabled=false`. The `GuardReservedConcurrency` value is ignored while the setting is disabled.

After deployment, copy the `WebhookUrl` stack output into the GitHub App's Webhook URL field.

The endpoint also supports a simple `GET` health response. GitHub webhook processing requires `POST` with a valid signature.

## Troubleshooting order

When a user reports trouble, diagnose from the outside in rather than broadening permissions immediately:

1. Did the App Check appear at all?
2. Is the App installed with access to the triggering repository?
3. Was the webhook delivered for a supported PR action?
4. Does the PR change a supported analysis suffix when a full scan is expected?
5. Can the base/head repository snapshots fit within beta limits?
6. If product scope is expected, is `.iaap/product.yaml` already on the triggering default branch?
7. Do all required members carry reciprocal trusted manifests?
8. Are owner and visibility boundaries compatible?
9. Does the App installation include every required member?
10. Can the relationship bundle complete within 20 MB?

See [`ADOPTION-PREREQUISITES.md`](ADOPTION-PREREQUISITES.md) for the full symptom-to-remediation table and support packet guidance.

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
- automatic cross-organization V1 federation;
- Marketplace or billing;
- FedRAMP/ATO claims;
- production-readiness claims.

The purpose is to prove useful GitHub-native architecture evidence, trusted multi-repository product coherence, trusted base/head continuity, and accountable review signals before investing in broader hosted-system complexity.
