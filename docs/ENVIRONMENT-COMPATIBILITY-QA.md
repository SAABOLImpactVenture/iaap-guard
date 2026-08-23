# Environment compatibility Q&A

This document defines how IaaP Guard V1 treats GitHub configuration, permissions,
network restrictions, and malformed repositories that cannot all be reproduced in one
reference environment. It is a compatibility and operator-response contract, not a
claim that every possible combination has been tested.

## Status vocabulary

| Status | Meaning |
|---|---|
| `VALIDATED` | Automated or recorded validation evidence exists for the condition. |
| `SUPPORTED` | The condition is inside the documented V1 contract. |
| `CONDITIONAL` | Support depends on the stated prerequisite or customer control. |
| `DEGRADED` | Guard can report a bounded result, but some evidence is unavailable. |
| `FAIL_CLOSED` | Guard must not produce an unqualified trusted result. |
| `UNVALIDATED` | The condition is documented but requires qualification before production use. |

## GitHub configuration and permission Q&A

### Does Guard work with every GitHub plan and deployment model?

No universal claim is made. The hosted V1 path is qualified only for the validated
GitHub.com operating path: same-repository pull requests without merge queues or custom
required-check behavior, where the repository can install the IaaP Guard GitHub App,
deliver supported pull-request events, expose immutable snapshots, and accept Check
publication. Fork-origin pull requests, merge queues, custom required-check rules,
GitHub Enterprise Server, enterprise-managed restrictions, and configurations that alter
App installation, webhook delivery, Checks publication, or repository archive access are
`UNVALIDATED` until exercised through the production-qualification process.

### What GitHub permissions are required?

Guard requires repository metadata read, contents read, pull-request read, and checks
read/write permissions. It does not require repository content-write, merge,
workflow-administration, provisioning, exception, or risk-acceptance authority. If a
required permission is withheld or later revoked, evaluation is `CONDITIONAL` and Guard
must report the missing prerequisite or fail closed; it must not infer inaccessible
evidence.

### What if the App is installed for selected repositories only?

Single-repository evaluation remains supported for an accessible repository. Trusted
multi-repository assessment requires App access to every registered member plus the
reciprocal, same-owner, visibility-compatible registrations defined in
[multi-repository products](MULTI-REPOSITORY-PRODUCTS.md). An inaccessible required
member makes the product result `INCOMPLETE` or fail closed.

### How do branch protection, rulesets, forks, archived repositories, and pull-request
policies affect Guard?

Guard does not bypass repository policy. It publishes a Check against the immutable pull
request head revision when GitHub permits it. Any configuration that prevents event
delivery, immutable snapshot access, or Check publication is a failed prerequisite.
Fork-origin pull requests, archived repositories, merge queues, custom required-check
rules, and enterprise rulesets must be qualified in the adopting organization when they
are part of the intended operating path.

### Are private, internal, and public repositories supported?

Repository visibility is supported only when the App has the required access. Automatic
V1 product federation is same-owner and same-visibility. Visibility changes or mixed
visibility product membership invalidate the trusted relationship until the documented
membership requirements are restored.

### What happens when a repository is renamed, transferred, deleted, or made
inaccessible during evaluation?

Guard must resolve immutable repository identity and revision evidence. A required
repository that cannot be resolved produces an `INCOMPLETE` or fail-closed result. Guard
does not silently substitute a repository with a similar name or reuse stale evidence as
current evidence.

## Network and platform Q&A

### What connectivity does the hosted App require?

GitHub must be able to deliver signed webhooks to the hosted endpoint, and the hosted
runtime must be able to call the required GitHub APIs. Customer proxies, private DNS,
TLS inspection, IP allowlists, egress restrictions, or enterprise firewalls that alter
that path are `CONDITIONAL` customer controls and require pre-production qualification.
Guard does not request customer-cloud network access.

### What happens during GitHub API throttling, timeouts, or outages?

Transport and platform availability are outside the deterministic V1 result contract.
Guard must not convert unavailable evidence into a successful trusted result. The
operator should expect a retryable delivery failure, missing Check, or bounded
`INCOMPLETE` result depending on where the failure occurs. Webhook redelivery or a new
pull-request event may be required after service recovery.

### What happens when the hosted runtime is unavailable?

No Check may be published. Absence of a current Check is not approval. Required-check
policy, monitoring, and incident response must prevent an unavailable Guard service from
being interpreted as a passing architecture decision.

## Malformed and adversarial repository Q&A

### What happens with invalid YAML, JSON, manifests, or unsupported rule versions?

Malformed required evidence, schema-invalid registration, conflicting membership, mixed
rule versions, or unresolvable immutable revisions must produce a normalized finding or
`INCOMPLETE`; otherwise Guard must fail closed without producing a trusted result. Guard
must not guess intent or relax validation to obtain a passing result.

### What happens with unsupported, binary, oversized, compressed, or unusually large
content?

The limits in [V1 Known Limits](KNOWN-LIMITS.md) are authoritative. Unsupported suffixes
are not analyzed. Required evidence outside a supported bound causes `INCOMPLETE` or a
fail-closed result. A pull request changing only unsupported suffixes receives the
documented `No relevant changes` result and must not be described as a full repository
assessment.

### What about symlinks, submodules, generated content, duplicate paths, or archive
anomalies?

Guard evaluates only evidence available through its supported immutable snapshot and
archive model. Content that cannot be represented safely as a supported regular file is
not trusted as evaluated product evidence. Any adopting organization that relies on
submodules, generated repositories, large-file storage, or nonstandard archive behavior
must record a qualification case before production use.

### Can malicious repository content change Guard's authority?

No repository content is authorization. Repository text, examples, comments, filenames,
and generated files are untrusted assessment input. They cannot grant permissions,
change frozen rules, authorize remediation, or override human review. Suspected parser,
archive, or isolation defects must be handled under [Security](../SECURITY.md).

## Qualification record

Each adopting environment should record the following for every material configuration:

| Field | Required record |
|---|---|
| Condition | GitHub, network, repository, or policy scenario |
| Status | One status from this document |
| Expected behavior | Continue, degrade, retry, mark `INCOMPLETE`, or fail closed |
| Operator action | Remediation, redelivery, policy change, or escalation |
| Evidence | Test run, Check URL, immutable revision, and validation record |
| Production gate | Blocking or non-blocking decision with owner |

Unknown, malformed, inaccessible, or unsupported inputs are not silently accepted. A
configuration is production-qualified only when its expected behavior and recovery path
have reproducible evidence.
