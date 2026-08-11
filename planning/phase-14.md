# Phase 14 — PR-Base Evidence Continuity

## Objective

Make Evidence Continuity visible automatically in the GitHub pull-request experience without expanding IaaP Guard authority.

## Key results

- Relevant PRs compare deterministic head evidence to deterministic PR-base evidence.
- The existing Architecture Check reports continuity status, Guard materiality, bounded disposition, compact deltas, and evidence digest.
- `review_required` remains advisory and does not alter existing repository Check conclusion semantics.
- Product-aware rendering preserves evidence-continuity output.
- No GitHub App permission expansion or persistent customer database is introduced.
