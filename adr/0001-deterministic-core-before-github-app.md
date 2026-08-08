# ADR 0001 — Build the deterministic core before the GitHub App

## Status
Accepted for Phase 8.

## Context

IaaP Guard is intended to become a GitHub-native Infrastructure-as-a-Product architecture and evidence guard. A GitHub App is the selected low-effort distribution experiment, but webhook hosting, installation flows, permissions, check-run APIs, billing, and dashboards do not prove that the underlying IaaP product knowledge is valuable.

The existing accelerator portfolio already contains deterministic product-boundary, authority, compatibility, and evidence controls that can be generalized without provisioning infrastructure.

## Decision

Build and prove a local deterministic IaaP Guard core before building the installable GitHub App adapter.

The core owns:

- component classification;
- structured parsing;
- versioned rule evaluation;
- normalized findings;
- scoring; and
- evidence output.

GitHub Actions and the GitHub App are adapters around that core and must not redefine rule semantics.

## Consequences

Positive:

- minimum effort is spent on the actual differentiated IP;
- dogfood can begin without hosted infrastructure;
- rules remain locally reproducible and testable;
- the same engine can support CLI, Action and App distribution;
- GitHub App permissions remain small.

Tradeoff:

- Phase 8 does not yet produce an externally installable App.

## Exit condition

Reconsider the adapter investment only after the deterministic fixture suite and six-repository dogfood demonstrate useful findings with an acceptable false-positive profile.
