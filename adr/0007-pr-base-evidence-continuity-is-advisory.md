# ADR 0007 — PR-base evidence continuity is advisory

## Status

Proposed for Phase 14.

## Context

Phase 13 established `evidence-manifest/v1` and the rule that evidence continuity is not authorization continuity. The GitHub App now needs a baseline that can be resolved automatically for pull requests without introducing persistent customer state or trusting a PR head to nominate its own prior authority.

GitHub already supplies an immutable base commit SHA for a pull request. That commit can be scanned with the same repository-scoped installation token used for the PR head.

A second decision is required: whether a `review_required` evidence-continuity result should change the existing `IaaP Guard / Architecture` Check conclusion.

## Decision

For Phase 14, IaaP Guard will compare deterministic PR-head evidence with deterministic PR-base evidence.

The baseline SHA will come from GitHub pull-request state, not from files or metadata controlled by the PR head.

The resulting evidence-continuity status will be published in the existing Architecture Check but will remain **advisory**. The repository scan result continues to own Check `success`, `neutral`, or `failure`.

A `review_required` continuity result therefore signals accountable human review without silently converting an otherwise successful repository architecture result into a new blocking policy.

## Rationale

This preserves several boundaries:

- the PR head cannot choose or rewrite its own baseline;
- the deterministic core remains stateless;
- no new GitHub App permissions are required;
- existing Check conclusion semantics remain stable for current consumers;
- evidence review can be introduced before an organization decides how to bind that review to branch protection or disposition workflows; and
- the tool does not infer that a PR-base commit represents legal, security, risk, exception, or institutional approval.

## Consequences

The GitHub App will download and scan both the PR head and PR base for IaaP-relevant changes. This adds bounded runtime work but avoids a persistent evidence database.

The Check will show the base revision, Guard materiality, continuity status, bounded disposition, evidence digest, and compact rule/finding deltas.

If the product-aware multi-repository layer later rewrites the Check output, it must preserve the evidence-continuity section.

A future phase may introduce a separate evidence-review Check or configurable blocking policy. That requires an explicit product/governance decision and must not be inferred from Phase 14.
