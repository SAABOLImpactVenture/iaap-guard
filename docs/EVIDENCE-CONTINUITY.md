# Evidence Continuity

## Status

**Phase 13 — Evidence Continuity Core: COMPLETE**  
**Phase 14 — PR-base Evidence Continuity: COMPLETE**

The deterministic evidence model is implemented, and the deployed GitHub App has live-proven both required PR-base continuity paths.

Canonical live evidence: [`Phase 14 live acceptance`](https://github.com/SAABOLImpactVenture/ai-powered-infrastructure-as-a-product/blob/main/artifacts/phase-14/live-acceptance.json).

## Purpose

IaaP Guard treats infrastructure governance as an evidence problem as well as a point-in-time rule-evaluation problem.

A repository can remain technically executable after the conditions that supported an earlier governance state have changed. IaaP Guard therefore answers a narrower, reconstructable question:

> What Guard evidence existed at the baseline, what Guard evidence exists now, what changed between them, and does that change require accountable human review?

IaaP Guard does **not** answer whether an action is legally, institutionally, operationally, security, compliance, deployment, exception, risk-acceptance, or contractually authorized. Evidence continuity is deliberately not an authorization oracle.

## Model

The deterministic evidence path is:

```text
baseline scan-result/v1 ─┐
                         ├─→ canonical digests
current scan-result/v1 ──┘        ↓
                         rule-state comparison
                                 ↓
                         finding-evidence delta
                                 ↓
                         Guard materiality
                                 ↓
                         evidence continuity
                                 ↓
                         bounded disposition
```

This creates `evidence-manifest/v1` using model `continuity/v1`.

The manifest records:

- immutable current and baseline revisions;
- SHA-256 digests of normalized Guard scan evidence;
- rule-catalog and scoring-model versions at both points;
- rule-state transitions;
- introduced, resolved, and unchanged finding evidence;
- whether the source revision changed;
- whether a Guard-material change was detected;
- whether evidence continuity is supported, requires review, or cannot yet be established;
- a bounded disposition; and
- an explicit statement that IaaP Guard did not determine authority.

## Status semantics

### `not_established`

No suitable baseline exists or the adapter cannot establish a trustworthy comparison.

Disposition: `baseline_required`.

The current manifest can still be retained as an evidence anchor.

### `supported`

The deterministic comparison did not produce a Guard-material rule/finding change relative to the baseline.

A new source revision may still exist. `supported` means only that the current state was re-evaluated without a material change detectable by the current IaaP Guard model.

Disposition: `no_additional_guard_review` when the current scan conclusion is also `success`.

This status is **not** equivalent to authorized, approved, compliant, safe, deployable, exception-covered, or risk accepted.

### `review_required`

The evidence contract changed in a way that IaaP Guard can identify, including:

- rule catalog changed;
- scoring model changed;
- one or more rule states changed; or
- finding evidence was introduced or resolved.

Disposition: `human_review_required`.

The tool does not decide who has disposition authority. That remains with the accountable governance system and humans outside IaaP Guard.

## Guard materiality

`changeAssessment.materiality` is intentionally bounded:

- `unknown_without_baseline` — no prior Guard evidence exists in the invocation;
- `no_guard_material_change_detected` — source may have changed, but deterministic Guard rule/finding state did not materially change;
- `guard_material_change_detected` — the ruleset, scoring model, rule state, or finding evidence changed.

The phrase **Guard materiality** is important. IaaP Guard does not claim that an undetected change is immaterial to law, policy, security, architecture, operations, finance, or organizational authority.

## Tamper-evident, not magically trusted

Each normalized scan is canonicalized and hashed with SHA-256. The evidence manifest is also canonicalized and hashed.

This makes modification detectable when the retained digest is compared with the document being reviewed. It does not by itself establish signer identity, non-repudiation, trusted timestamping, or external custody.

Those capabilities can be layered later through artifact attestations, signed provenance, an external evidence store, or another governed system without changing the deterministic comparison model.

## CLI

Create the first evidence anchor and retain the current normalized scan as the next baseline:

```bash
PYTHONPATH=src python3 -m iaap_guard.cli evidence . \
  --repository example/platform-product \
  --revision 1111111111111111111111111111111111111111 \
  --scan-output prior-scan-result.json \
  --format json \
  --output baseline-evidence.json
```

The first invocation reports `not_established` because there is no baseline. `baseline-evidence.json` is the reconstructable evidence manifest; `prior-scan-result.json` retains the normalized `scan-result/v1` needed for the next comparison.

Compare current state to the retained baseline scan result and retain the new scan for the following evaluation:

```bash
PYTHONPATH=src python3 -m iaap_guard.cli evidence . \
  --repository example/platform-product \
  --revision 2222222222222222222222222222222222222222 \
  --baseline prior-scan-result.json \
  --scan-output current-scan-result.json \
  --format markdown
```

Use `--format json` for the normalized `evidence-manifest/v1` contract.

The command exits successfully only when continuity is `supported` and the current scan conclusion is `success`. A missing baseline, material evidence change, WARNING, or FAIL requires review and returns a non-zero exit status.

## GitHub PR-base baseline

The GitHub App provides a stronger adapter-specific baseline rule than an arbitrary local file:

```text
GitHub PR base SHA → deterministic scan → baseline scan-result/v1
GitHub PR head SHA → deterministic scan → current scan-result/v1
                                      ↓
                            evidence-manifest/v1
                                      ↓
                               continuity/v1
```

The proposed change cannot nominate its own baseline. GitHub pull-request state supplies the immutable base revision.

For Check rerequests, Guard resolves the current PR again before selecting the base/head pair.

See [`PR-BASE-EVIDENCE-CONTINUITY.md`](PR-BASE-EVIDENCE-CONTINUITY.md).

## Live Phase 14 proof

The deployed App was tested on one fresh pull request from current main.

### Baseline case

A non-Guard-material change produced:

- architecture conclusion: `PASS`;
- score: `100`;
- findings: `0`;
- Evidence Continuity: `SUPPORTED`;
- materiality: `no_guard_material_change_detected`;
- disposition: `no_additional_guard_review`; and
- zero rule-state or finding deltas.

### Controlled material-change case

A subsequent controlled change on the same PR produced:

- architecture conclusion: `WARNING`;
- score: `67`;
- finding: `IAP-P004`;
- Evidence Continuity: `REVIEW REQUIRED`;
- materiality: `guard_material_change_detected`;
- disposition: `human_review_required`;
- four rule-state transitions; and
- one introduced finding.

The proof confirms that Evidence Continuity is operating in the deployed App rather than only in unit tests or local CLI output.

## Relationship to multi-repository products

Phase 12 established live-proven reciprocal, bounded product membership across repositories. The GitHub App preserves the triggering repository's Evidence Continuity section when it enriches the Check with product-level context.

Current composition is:

```text
Trigger repository architecture
        +
Trigger repository PR-base Evidence Continuity
        +
Trusted multi-repository Product Assessment
        +
Product Improvement Plan when needed
```

Current temporal continuity remains repository-scoped. A future product-wide evidence graph could compare changing member evidence revisions across time, but that is a separate product decision rather than an implication hidden inside Phase 12 or Phase 14.

## Relationship to exceptions and escape rate

Evidence Continuity provides the temporal substrate for future exception and escape-rate features.

An exception should eventually be able to point to:

```text
exception identity
      ↓
control / rule scope
      ↓
baseline evidence digest
      ↓
conditions asserted at approval
      ↓
current evidence digest
      ↓
Guard-detected material change
      ↓
revalidation / expiration / human disposition
```

IaaP Guard should record the existence and evidence trail of an exception without deciding whether the person or system asserting the exception possessed valid authority. Trusted authority evidence must come from a separately governed source rather than being silently promoted from an untrusted PR head.

## Adoption barriers

Evidence Continuity depends on successful bounded scans of the relevant GitHub base/head states.

Common barriers include:

- the App is not installed or the webhook is not delivered;
- the pull request changes no supported analysis suffix, so the full continuity path is intentionally skipped;
- the repository snapshot exceeds beta bounds; or
- a suitable GitHub base revision cannot be scanned.

See [`ADOPTION-PREREQUISITES.md`](ADOPTION-PREREQUISITES.md) for symptom-to-remediation guidance.

## Product boundary

IaaP Guard is an evidence guard, not a compliance oracle.

It can establish what it evaluated, under which Guard rules, at which immutable revisions, how the resulting evidence changed, and whether its own evidence model supports continuity.

It cannot establish that legal or institutional authority existed, that an approval remains legally valid, that a deployment is permissible, that an exception remains valid, or that a human reviewer has disposition authority. Those decisions remain external and accountable.
