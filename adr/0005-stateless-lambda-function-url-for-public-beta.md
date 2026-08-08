# ADR 0005 — Use a stateless Lambda Function URL for the public GitHub App beta

**Status:** Accepted for Phase 10 beta.

## Context

Phase 9 proved the deterministic IaaP Guard core and GitHub Action across the six-repository IaaP portfolio. Phase 10 must prove a normal public GitHub App installation and Check Run experience without prematurely building a SaaS control plane, database, billing system, customer credential store, or second rule engine.

The deterministic core is already Python and requires only a repository snapshot plus explicit repository/revision identity. GitHub supplies the App identity, installation model, webhook delivery, short-lived installation token, and Check Run surface.

## Decision

Use an AWS Lambda function with a public Lambda Function URL as the first hosted GitHub App webhook adapter.

The runtime:

1. validates `X-Hub-Signature-256` before processing a delivery;
2. creates a short-lived RS256 GitHub App JWT;
3. exchanges it for an installation token scoped to the triggering repository and the minimum required permissions;
4. reads pull-request metadata/files and an immutable repository snapshot when relevant;
5. invokes the existing deterministic IaaP Guard core;
6. creates or updates `IaaP Guard / Architecture` as a GitHub Check; and
7. persists no customer database state.

The App private key and webhook secret are stored outside the repository in AWS Secrets Manager. The Lambda role can read only those two configured secrets.

## Why this option

- reuses the existing Python core directly;
- provides a public HTTPS webhook with very little infrastructure;
- requires no always-on service or database;
- keeps operating cost near zero at beta traffic levels;
- keeps GitHub distribution concerns outside the deterministic rule engine;
- can be replaced later without changing `scan-result/v1`, the rule catalog, or Check semantics.

## Security boundaries

The Function URL uses public invocation because GitHub must reach it. Public transport reachability is not trusted as webhook identity; the application-layer HMAC is mandatory.

The GitHub installation token is minted per handled delivery, narrowed to the triggering repository, and granted only Contents read, Pull requests read, and Checks write. No personal access token is used.

The adapter receives no cloud/Kubernetes/TFE/AI credentials belonging to the installed repository and no repository content-write, merge, workflow, or administration authority.

## Consequences

Positive:

- smallest hosted beta consistent with the existing Python implementation;
- no persistent customer-state system to operate or secure;
- public and private/internal GitHub repositories can use the same App installation model;
- GitHub App identity replaces the internal-Action sharing limitation discovered in Phase 9.

Tradeoffs:

- repository snapshots must fit explicit beta archive/ephemeral-storage limits;
- cold starts and synchronous execution are acceptable for beta but may require later measurement;
- fork-based pull-request behavior is not claimed until separately tested;
- Lambda is a reference hosting implementation, not a permanent product dependency.

## Exit condition

Keep this hosting model only while it satisfies the Phase 10 installability, correctness, security, latency, and operating-cost evidence. A later hosting change must preserve the same deterministic core and authority boundaries.
