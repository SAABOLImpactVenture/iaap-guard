# Adoption Readiness / Preflight

## Status

**Phase 15 — COMPLETE.** The implementation is merged, deployed, live-accepted,
and backed by retained READY → BLOCKED → READY evidence.

## Product question

Adoption Readiness answers: **Can Guard reliably evaluate the intended repository or
logical product scope, and if not, what exact obstacle must the user remove?**

It is diagnostic, not an architecture rule, authorization decision, or remediation
engine. Readiness does not change architecture scoring, Check conclusions,
`continuity/v1`, or `product-assessment/v1`.

## Local preflight

Run without GitHub credentials or network access:

```bash
PYTHONPATH=src python3 -m iaap_guard.cli preflight . \
  --repository owner/name \
  --format markdown
```

Use `--format json` for `readiness-report/v1` and `--output PATH` to retain it. A blocked
report exits 1; ready and advisory reports exit 0.

Local preflight checks path/readability, supported suffix discovery, the 1 MB per-file
analysis bound, recognizable IaaP evidence, and optional `.iaap/product.yaml` validity.
When a manifest exists, `--repository owner/name` enables self-membership validation.
GitHub access, visibility, reciprocal trusted manifests, immutable default-branch SHAs,
and member acquisition remain explicitly not applicable/unevaluated locally, so a valid
local registration can be `READY` without pretending the GitHub checks ran.

A normal single repository needs no product manifest:

```text
Repository mode: READY
Multi-repository product registration: NOT CONFIGURED
No action required unless this repository is part of a logical product spanning multiple repositories.
```

## GitHub-aware product readiness

When trusted registration exists, the existing App federation path diagnoses:

- same-owner and same-visibility boundaries;
- App installation access and readable repository metadata;
- a usable default branch and trusted default-branch manifest;
- matching product identity and complete reciprocal membership signature;
- immutable default-branch SHA resolution;
- bounded evidence acquisition under repository-specific `contents:read` authority;
- required-member completeness; and
- whether relationship evaluation can complete within existing bounds.

Required unavailable members block readiness. Optional unavailable members are advisory
where existing product semantics permit. If readiness is blocked, the Check explains the
barrier instead of presenting incomplete acquisition as healthy product evidence.

No new Check is created. `IaaP Guard / Architecture` remains authoritative for the Check
conclusion; readiness is appended as advisory context.

## Stable requirement IDs

| ID | Requirement |
|---|---|
| `IAP-RDY001` | Local repository path exists and is readable |
| `IAP-RDY002` | Supported analysis artifacts are discoverable |
| `IAP-RDY003` | Relevant files fit the per-file bound |
| `IAP-RDY004` | Recognizable IaaP evidence is present |
| `IAP-RDY005` | Optional product manifest is valid |
| `IAP-RDY006` | Trigger repository registers itself |
| `IAP-RDY007` | GitHub-only trust/acquisition checks are identified locally |
| `IAP-RDY101` | Trusted triggering registration is valid and self-registering |
| `IAP-RDY102` | Product member is within the same-owner boundary |
| `IAP-RDY103` | Product member visibility matches the trigger |
| `IAP-RDY104` | App access and repository metadata/default branch are available |
| `IAP-RDY105` | Trusted member default branch contains the product manifest |
| `IAP-RDY106` | Product identity and membership are reciprocal |
| `IAP-RDY107` | Member resolves to an immutable default-branch SHA |
| `IAP-RDY108` | Immutable member evidence can be acquired |
| `IAP-RDY109` | All required members are ready |
| `IAP-RDY110` | Bounded relationship evaluation can complete |

IDs diagnose setup prerequisites and never reuse architecture rule IDs.

## Contract and determinism

`schemas/readiness-report.schema.json` is a strict normalized contract. It contains no
timestamp. Requirements and members use deterministic ordering. The local core makes no
network calls, does not execute scanned code, and does not use AI decisions.

Each requirement includes status, observed state, impact, remediation, severity,
blocking classification, and applicable repository/path. Reports explicitly state the
authority and product boundary.

## Readiness versus continuity

Readiness asks whether Guard can evaluate the intended scope. Evidence Continuity asks
whether Guard-observed evidence materially changed between the trusted PR base and head.
They may differ: architecture can pass and continuity can be supported while product
readiness is blocked by an inaccessible required member.

## Product progression

```text
Prerequisite knowledge
        ↓
Deterministic preflight
        ↓
Actionable barrier diagnosis
        ↓
Architecture evaluation
        ↓
Evidence Continuity
        ↓
Product Assessment
        ↓
Improvement Plan
```
