# Evidence Continuity

IaaP Guard treats infrastructure governance as an evidence problem as well as a point-in-time rule-evaluation problem.

A repository can remain technically executable after the conditions that supported an earlier governance state have changed. IaaP Guard therefore needs to answer a narrower, reconstructable question:

> What Guard evidence existed at the baseline, what Guard evidence exists now, what changed between them, and does that change require accountable human review?

IaaP Guard does **not** answer whether an action is legally, institutionally, operationally, or contractually authorized. Evidence continuity is deliberately not an authorization oracle.

## Model

The Phase 13 deterministic evidence path is:

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
- SHA-256 digests of the normalized Guard scan evidence;
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

No baseline was supplied. The current manifest can be retained as an evidence anchor, but continuity cannot yet be evaluated.

Disposition: `baseline_required`.

### `supported`

A baseline was supplied, the same rule catalog and scoring model apply, and the current deterministic evaluation did not produce a rule-state or finding-evidence change relative to the baseline.

A new source revision may still exist. `supported` means only that the current state was re-evaluated without a material change detectable by the current IaaP Guard model.

Disposition: `no_additional_guard_review` when the current scan conclusion is also `success`.

This status is **not** equivalent to authorized, approved, compliant, safe, deployable, or risk accepted.

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
- `no_guard_material_change_detected` — source may have changed, but the deterministic Guard rule/finding state did not materially change;
- `guard_material_change_detected` — the ruleset, scoring model, rule state, or finding evidence changed.

The phrase **Guard materiality** is important. IaaP Guard does not claim that an undetected change is immaterial to law, policy, security, architecture, operations, finance, or organizational authority.

## Tamper-evident, not magically trusted

Each normalized scan is canonicalized and hashed with SHA-256. The evidence manifest is also canonicalized and hashed.

This makes modification detectable when the retained digest is compared with the document being reviewed. It does not by itself establish signer identity, non-repudiation, trusted timestamping, or external custody.

Those capabilities can be layered later through artifact attestations, signed provenance, an external evidence store, or another governed system without changing the deterministic comparison model.

## CLI

Create the first evidence anchor:

```bash
PYTHONPATH=src python3 -m iaap_guard.cli evidence . \
  --repository example/platform-product \
  --revision 1111111111111111111111111111111111111111 \
  --format json \
  --output baseline-evidence.json
```

The first invocation reports `not_established` because there is no baseline. Retain the corresponding `scan-result/v1` JSON as the baseline input for a later comparison.

Compare current state to a retained baseline scan result:

```bash
PYTHONPATH=src python3 -m iaap_guard.cli evidence . \
  --repository example/platform-product \
  --revision 2222222222222222222222222222222222222222 \
  --baseline prior-scan-result.json \
  --format markdown
```

Use `--format json` for the normalized `evidence-manifest/v1` contract.

The command exits successfully only when continuity is `supported` and the current scan conclusion is `success`. A missing baseline, material evidence change, WARNING, or FAIL requires review and returns a non-zero exit status.

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

## Multi-repository products

Phase 12 established reciprocal, bounded product membership across repositories. Evidence Continuity can use the same trust boundary later to build a product-level evidence graph.

The intended direction is:

```text
Product
 ├─ repository evidence manifest
 ├─ repository evidence manifest
 ├─ repository evidence manifest
 ├─ compatibility evidence
 └─ product assessment
          ↓
  product evidence continuity
```

A change in one member repository can then cause product evidence to require revalidation without granting that member repository authority to redefine the product boundary or another repository's authority.

## Product boundary

IaaP Guard is an evidence guard, not a compliance oracle.

It can establish what it evaluated, under which Guard rules, at which immutable revisions, how the resulting evidence changed, and whether its own evidence model supports continuity.

It cannot establish that legal or institutional authority existed, that an approval remains legally valid, that a deployment is permissible, or that a human reviewer has disposition authority. Those decisions remain external and accountable.
