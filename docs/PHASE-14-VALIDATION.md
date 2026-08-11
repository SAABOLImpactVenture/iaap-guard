# Phase 14 Validation Contract

Phase 14 is accepted only when the existing repository validation suite remains green and the PR-base evidence adapter proves both continuity paths:

1. identical Guard state across different immutable revisions reports `supported` and preserves the repository Check conclusion;
2. a Guard-material rule/finding change reports `review_required`, requests human review, and still preserves the existing repository Check conclusion because evidence continuity is advisory in this phase;
3. the final Check states that evidence continuity is not authorization continuity; and
4. product-aware Check rendering preserves the evidence-continuity layer when registered multi-repository product context is also present.

No GitHub App permission expansion is permitted for Phase 14.
