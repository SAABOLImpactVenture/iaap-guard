# Public Guard Assurance Evidence

## Purpose

This ledger maps current public Guard claims to minimum-necessary, sanitized evidence.
It does not publish private implementation coordinates, raw operational logs, customer
content, credentials, or internal topology. The machine-readable record is
[`public-guard-assurance.json`](../artifacts/remediation-r1/public-guard-assurance.json).

## Claim-to-evidence matrix

| Claim | Result | Public or sanitized evidence | Explicit limit |
|---|---|---|---|
| Current hosted negative-result publication | **VERIFIED** | Closed, unmerged [public probe PR #133](https://github.com/SAABOLImpactVenture/ai-powered-infrastructure-as-a-product/pull/133); WARNING head `1faaae1a5da9d4c4c74d8a599f3a8b0088be2210`, neutral Check `99733468182`, evidence digest `sha256:b6ad49fa12a17290802099fb258ab6355ceae477f8ee0ee7bbf4f372ca7e9ce8`; FAIL head `d7abf62086c3e26fae5f02209ded5ddd470d25d7`, failure Check `99733893114`, evidence digest `sha256:c575e7e2939f0773f6ecd31a1c4c3462e7b923df5bd04f1a5e8f91846ccc3a26` | Synthetic public repository only; no customer data, pilot, or production authorization. |
| Protected deployment-log retention | **VERIFIED WITH SANITIZATION** | Five protected identity, pre-verification, plan, deploy, and post-verification logs were retained; their SHA-256 digests and aggregate canonical-record digest are in the machine-readable record | Raw logs, workflow/job identifiers, cloud coordinates, and secret-reference topology remain private. This is deployment evidence retention, not a customer logging or retention guarantee. |
| Hosted application logging and retention | **NOT ESTABLISHED** | No qualifying public evidence | Request-log completeness, redaction, retention, searchability, and incident use were not independently exercised. |
| Alarm status | **POINT-IN-TIME ONLY** | Three configured alarms reported `OK` in the retained observation; canonical sanitized-record digest `sha256:ea6d11006272627f14931f4d56975178911afa315c49f86b467d60ca6e5049a1` | No alert was deliberately triggered; delivery, escalation, and response were not verified. |
| Representative concurrency and endurance | **NOT ESTABLISHED** | No qualifying public evidence | No throughput, simultaneous-evaluation, throttling, backlog-recovery, or endurance claim is made. |
| Rollback readiness | **PROCEDURE AND TARGET RETAINED** | A known-good target and controlled procedure were retained | Rollback was not executed; rollback completion and recovery time are not established. |
| Clean-adopter installation mechanics | **VERIFIED** | Closed [adopter PR #1](https://github.com/SAABOLImpactVenture/iaap-guard-adopter-validation/pull/1) at head `7bb6f811a7001233aaed861351eaf755df91b902`, neutral Check `95076939126` | Same-organization test; not independent adoption, customer value, production use, or a non-neutral clean-adopter proof. |
| Production qualification | **NOT ESTABLISHED** | [Production readiness and operations Q&A](PRODUCTION-READINESS-QA.md) defines the missing gates | No SLA, controlled pilot, production-readiness, compliance, or risk-acceptance claim. |

## Phase-completion evidence

| Completion statement | Minimum public evidence | Reproducibility limit |
|---|---|---|
| Phase 9 deterministic portfolio dogfood | [`artifacts/phase-9/index.json`](../artifacts/phase-9/index.json) and its immutable repository-result, mutation, repeatability, and scorecard records | Portfolio-owned fixtures and repositories; not independent customer adoption. |
| Phase 10 public GitHub App beta | [Phase 10 beta scorecard](https://github.com/SAABOLImpactVenture/ai-powered-infrastructure-as-a-product/blob/main/artifacts/phase-10/beta-scorecard.json) and [public live Check supplement](https://github.com/SAABOLImpactVenture/ai-powered-infrastructure-as-a-product/blob/main/artifacts/phase-10/public-live-check-run-supplement.json) | Historical beta proof; current negative-result publication is established separately by the R1 probe above. |
| Phase 12 reciprocal product federation | [Live federation acceptance](https://github.com/SAABOLImpactVenture/ai-powered-infrastructure-as-a-product/blob/main/artifacts/phase-12/live-federation-acceptance.json) | Two repositories in one organization; not universal federation or production scale. |
| Phase 14 PR-base Evidence Continuity | [Live acceptance](https://github.com/SAABOLImpactVenture/ai-powered-infrastructure-as-a-product/blob/main/artifacts/phase-14/live-acceptance.json) and [Phase 14 validation](PHASE-14-VALIDATION.md) | Advisory continuity only; not authorization continuity. |
| Phase 15 READY → BLOCKED → READY | [Acceptance campaign](https://github.com/SAABOLImpactVenture/ai-powered-infrastructure-as-a-product/blob/main/artifacts/phase-15/acceptance-campaign.json) and [Phase 15 validation](PHASE-15-VALIDATION.md) | Controlled same-organization product; no external pilot. |
| Phase 16 bounded beta closure | [Phase 16 validation](PHASE-16-VALIDATION.md) and closed [adopter PR #1](https://github.com/SAABOLImpactVenture/iaap-guard-adopter-validation/pull/1) | Point-in-time operational observation and same-organization installation mechanics; capacity, endurance, alert response, rollback execution, and disaster recovery remain open. |
| Phase 17 unfamiliar-code campaign and V1 freeze | [`external-adoption.json`](../artifacts/phase-17/external-adoption.json), [`adjudication.json`](../artifacts/phase-17/adjudication.json), and [Phase 17 validation](PHASE-17-VALIDATION.md) | Read-only unfamiliar-code evaluation; the App was not installed in adopter repositories and customer value was not tested. |
| Phase 18 bounded V1 publication | Immutable [`v1.0.0`](https://github.com/SAABOLImpactVenture/iaap-guard/tree/v1.0.0), [Phase 18 validation](PHASE-18-VALIDATION.md), and [V1 Contract Freeze](V1-CONTRACT-FREEZE.md) | Historical tag includes the retired CLI and composite Action; hosted App is the only supported current distribution. No GitHub Release object is claimed. |

## Maintenance status

`v1.0.1` remains fixed at its original commit. A tag and published GitHub Release
object currently exist for that maintenance baseline. Repository publication is not
runtime activation and does not establish a new distribution path, pilot authority,
production qualification, or product authority.

The `1.0.2` maintenance candidate removes live nonpublic-producer and cloud-account
coordinates from the public validator. It uses an explicit public-repository allowlist,
generic cloud-coordinate detection, and synthetic negative fixtures. It does not move
or recreate `v1.0.1`.

## Version identities

The public V1 contract remains:

- rule catalog: `iaap-guard/v0.1.2`;
- planning catalog: `iaap-planning/v0.1.0`;
- repository planning schema: `planning-report/v1`;
- product planning schema: `product-planning-report/v1`; and
- public maintenance candidate: `1.0.2`.

The planning-catalog version and immutable public blob are frozen in
[V1 Contract Freeze](V1-CONTRACT-FREEZE.md). This public ledger intentionally identifies
public inputs and outputs, not private producer revisions or deployment topology.

## Authority boundary

These records establish bounded technical observations only. They do not authorize a
deployment, pilot, customer-data exercise, exception, compliance conclusion, risk
acceptance, repository mutation, remediation, or infrastructure execution.
