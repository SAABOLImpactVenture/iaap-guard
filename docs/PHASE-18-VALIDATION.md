# Phase 18 Validation

## Status

**COMPLETE — the bounded IaaP Guard V1 product is published from the frozen contracts.**

## Release candidate

Version `1.0.0` was the first bounded V1 release. At issuance it included the
deterministic core, versioned rules and schemas, CLI, composite GitHub Action, public
GitHub App adapter, adoption preflight, evidence continuity, product federation, and
advisory planning behavior already proven in Phases 8–17. The public CLI and composite
Action were subsequently retired; the hosted GitHub App is the only supported current
distribution path.

The release adds no new rule semantics, score authority, GitHub App permission,
infrastructure authority, or product scope.

## Acceptance chain

The V1 declaration rests on retained evidence:

- Phase 9 deterministic portfolio dogfood and mutation evidence;
- Phase 10 public App deployment and live installation;
- Phase 12 reciprocal multi-repository federation and remediation;
- Phase 14 immutable PR-base Evidence Continuity;
- Phase 15 READY → BLOCKED → READY adoption acceptance;
- Phase 16 operational, security, clean-adopter, and boundary closure; and
- Phase 17 immutable three-cloud external-adoption evidence and finding adjudication.

The compatibility and authority surface is frozen in
[`V1-CONTRACT-FREEZE.md`](V1-CONTRACT-FREEZE.md). Current support and known limits
are published in [`SUPPORT.md`](SUPPORT.md) and
[`KNOWN-LIMITS.md`](KNOWN-LIMITS.md). The public composite Action is retired; use the
[hosted GitHub App](https://github.com/apps/iaap-guard).

## Release mechanics

The protected release pull request carried the `1.0.0` version and completion
declaration through deterministic validation, dogfood, dependency review, CodeQL, and
the repository's branch policy. Tag `v1.0.0` identifies the resulting historical release
commit. Current maintenance must not restore either root Action manifest or describe the
historical Action as a supported path.

## Completion declaration

IaaP Guard product development is complete at V1. Future work in this repository is
compatible maintenance or an explicitly governed successor—not an invitation to absorb
the separate products that follow it.

## Boundary confirmation

V1 remains deterministic, advisory, stateless at its product center, and
least-privilege. It does not ingest organizational OKRs, manage work or enterprise
strategy, execute infrastructure, acquire customer infrastructure credentials, mutate
repositories, remediate or authorize automatically, certify compliance, or claim
production readiness.
