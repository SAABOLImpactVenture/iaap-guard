# ADR 0006 — Evidence continuity does not determine authority

## Status

Accepted for Phase 13.

## Context

A point-in-time architecture scan can establish what IaaP Guard observed under a specific rule catalog at an immutable revision. It cannot by itself establish that the conditions supporting an earlier governance decision still apply later.

Infrastructure can remain technically executable after repository state, policy state, findings, exceptions, or other supporting conditions change. A governance system therefore needs reconstructable evidence across time, not only a PASS/FAIL result at one moment.

At the same time, allowing IaaP Guard to infer that technical evidence equals legal or institutional authority would collapse an important governance boundary. A repository scanner cannot prove that an approver possessed authority, that an exception remains valid, or that a deployment is legally permitted.

## Decision

IaaP Guard will introduce a deterministic `evidence-manifest/v1` contract with model `continuity/v1`.

The model may:

- hash normalized Guard scan evidence;
- compare immutable current and baseline revisions;
- compare rule-catalog and scoring-model versions;
- identify rule-state transitions;
- identify finding-evidence changes;
- classify bounded **Guard materiality**;
- determine whether Guard evidence continuity is supported, not established, or requires review; and
- require accountable human review when Guard evidence materially changes.

The model must not:

- determine legal or institutional authorization;
- infer authority from technical executability;
- treat historical approval as proof of continuing applicability;
- decide who has exception or disposition authority;
- silently promote authority claims from an untrusted PR head; or
- describe `supported` evidence continuity as approved, compliant, safe, deployable, or authorized.

Any future authority or exception evidence must be sourced through an explicitly governed trust boundary and recorded as evidence, not converted by IaaP Guard into an authority determination.

## Consequences

Evidence continuity becomes a first-class product capability rather than an incidental log artifact.

The deterministic core remains stateless: the caller supplies any baseline evidence, so Phase 13 does not require a customer database.

The GitHub App can later compare PR-head evidence with a trusted baseline or base-revision result without changing the core evidence model.

Future exception aging, revalidation, escape-rate analysis, signed attestations, and product-level evidence graphs can build on the same manifest while preserving human governance authority.
