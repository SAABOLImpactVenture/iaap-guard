# Production readiness and operations Q&A

IaaP Guard V1 has validated deterministic product contracts, but contract correctness is
not the same as long-running production readiness. This document defines the evidence an
operator must produce before calling a specific hosted deployment production-qualified.
It does not declare the reference deployment production-ready and does not change the
frozen V1 contract or authority boundary.

## What must be true before a deployment is called production-qualified?

The operator must have reproducible evidence for:

- environment compatibility and required GitHub permissions;
- representative capacity, concurrency, throttling, and endurance behavior;
- monitoring, alerting, support ownership, and incident escalation;
- safe release, rollback, and dependency-update procedures;
- event replay or redelivery and failed-assessment recovery;
- retention, backup, restoration, and disaster-recovery decisions for every persistent
  operational component; and
- a clean-room installation and recovery exercise completed without developer-only
  knowledge.

Passing deterministic tests or meeting installation prerequisites alone is insufficient.

## Reliability Q&A

### What availability does V1 promise?

V1 publishes no service-level agreement or universal availability target. The
deterministic contracts describe result behavior; hosting availability remains an
operational concern. An adopting operator must define service-level indicators and an
objective for webhook receipt, evaluation completion, Check publication, and recovery.

### How is long-running reliability demonstrated?

Through recorded endurance testing over a representative event mix, including normal
pull requests, irrelevant changes, malformed inputs, multi-repository products, rate
limits, dependency failures, and repeated deliveries. Evidence must include error rate,
latency, resource use, queue or concurrency pressure, and unresolved event count.

### Is a missing Guard Check equivalent to approval?

No. A current successful Check is affirmative evidence; absence, timeout, or stale-revision
evidence is not approval. Branch or organizational policy should encode that distinction
where Guard is required.

## Scaling and capacity Q&A

### What scale is supported?

The public V1 contract defines repository, archive, file, relationship-bundle, and product
member limits in [V1 Known Limits](KNOWN-LIMITS.md). It does not publish a universal
tenant-throughput or concurrency guarantee. Each deployment must qualify expected peak
webhook rate, simultaneous evaluations, GitHub API budget, execution duration, and
failure backlog.

### How should overload behave?

Overload must be visible and bounded. It must not create a false successful result,
silently drop required evidence, or publish a Check against the wrong revision. The
operator must document throttling, backpressure, retry, duplicate-delivery, timeout, and
dead-letter behavior for the deployed adapter.

### When is additional capacity required?

Capacity review is required when observed utilization, throttling, timeout, backlog, or
latency approaches the operator's documented threshold; when repository limits change;
or before onboarding a materially larger organization or product portfolio.

## Upgrade and release Q&A

### What may change without a new Guard contract version?

Only the changes allowed by [V1 Contract Freeze](V1-CONTRACT-FREEZE.md), including
semantics-preserving defect fixes, documentation, compatible adapters, and security or
dependency updates that do not expand authority. Backward-incompatible behavior requires
an explicitly versioned successor and migration guidance.

### What is the safe upgrade sequence?

The release owner must validate schemas, rules, deterministic core compatibility,
adapter/runtime behavior, and consumption of the published GitHub Check contract before
promotion. A release record must identify immutable versions, test evidence, change risk,
rollback target, and the person approving promotion. Production promotion must never
rely only on a mutable branch name.

### What is required for rollback?

A known-good immutable runtime and compatible contract artifacts, a documented trigger,
an authorized operator, and a post-rollback validation case. Rollback must preserve
evidence provenance and must not relabel earlier results as having been produced by a
different version.

## Recovery and continuity Q&A

### How are failed or missed assessments recovered?

Recovery must preserve the original repository identity and immutable revision. Depending
on the failure point, the operator may use GitHub webhook redelivery or create a new
supported event after recovery. Duplicate delivery must not create contradictory trusted
results. Manual fabrication of a passing Check is not an accepted recovery method.

### What must be backed up?

The V1 GitHub App evaluation path is designed as stateless, while GitHub ordinarily
retains the Check and repository evidence. Operators must not assume that evidence remains
available after repository deletion, transfer, retention expiry, or loss of App access.
They must inventory Guard results, evaluated source evidence or immutable references, and
every deployment-specific persistent component, including configuration, secrets
metadata, release manifests, monitoring, incident records, and any queues or dead-letter
stores. Each evidence class and component needs an explicit retain, export, back up,
reconstruct, or exclude decision with an accountable owner and retention period.

### What disaster-recovery evidence is required?

A timed exercise must demonstrate restoration or reconstruction of the hosted adapter,
verification of GitHub identity and permissions, processing of a known validation case,
publication against the correct head revision, and reconciliation of any events missed
during the outage. Recovery-time and recovery-point objectives belong to the deployment
operator, not the deterministic Guard contract.

## Monitoring and support Q&A

### What should be monitored?

At minimum: signed webhook receipt, signature or identity rejection, event age,
evaluation completion, Check publication, latency, error and timeout rates, concurrency
or queue pressure, GitHub throttling, malformed-input frequency, `INCOMPLETE` frequency,
and deployed version. Monitoring must not expose credentials, webhook bodies, or private
repository content.

### Who owns incidents?

Every qualified deployment must name a service owner, release owner, security contact,
and escalation path. Public product questions and private security reports follow
[Support](SUPPORT.md); public issues must not contain private customer evidence or hosted
implementation details.

### What operational runbooks are required?

Runbooks must cover unavailable endpoint, signature failure, revoked App access, GitHub
API throttling, stuck or duplicate event, Check publication failure, malformed repository,
capacity exhaustion, rollback, secret rotation, dependency vulnerability, and regional or
provider outage. Each runbook needs detection, containment, recovery, validation, owner,
and escalation steps.

## Production qualification record

| Gate | Minimum evidence | Blocking? |
|---|---|---|
| Compatibility | Completed environment cases from [Environment compatibility Q&A](ENVIRONMENT-COMPATIBILITY-QA.md) | Yes |
| Functional | Clean-room install plus representative positive, negative, incomplete, and fail-closed cases | Yes |
| Capacity | Peak-load and backlog recovery test | Yes |
| Endurance | Sustained representative workload with agreed error and latency thresholds | Yes |
| Observability | Dashboards, alerts, log-redaction review, and alert-response exercise | Yes |
| Release | Immutable promotion, compatibility verification, and rollback exercise | Yes |
| Recovery | Missed-event reconciliation and disaster-recovery exercise | Yes |
| Support | Named owners, severity model, escalation path, and runbooks | Yes |
| Security | Private reporting path, dependency process, and open-risk review | Yes |

Until every applicable blocking gate has dated evidence and an accountable approver, the
deployment remains validation or beta scope. Evidence is not deployment, compliance,
exception, or risk-acceptance authorization.
