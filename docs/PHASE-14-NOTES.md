# Phase 14 Notes

This phase intentionally composes existing contracts instead of changing the Phase 13 evidence model:

- `scan-result/v1` remains the repository architecture evidence contract;
- `evidence-manifest/v1` / `continuity/v1` remains the temporal comparison contract;
- the PR base is an adapter-selected baseline, not a new authorization source; and
- the existing GitHub Check conclusion remains owned by the repository scan.

The implementation is therefore a GitHub runtime integration, not a new rule catalog or scoring model.
