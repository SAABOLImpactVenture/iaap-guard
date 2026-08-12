# Phase 15 Validation

## Status

**IN REVIEW — automated implementation validation is not live acceptance.**

## Automated evidence

`tests/test_phase15_readiness.py` covers:

- single-repository readiness without product registration;
- supported and absent meaningful evidence;
- malformed, self-omitting, duplicate, over-12, and multiple-primary manifests;
- valid local registration with GitHub checks explicitly unevaluated;
- complete GitHub-aware product readiness;
- inaccessible, visibility-mismatched, missing-manifest, and non-reciprocal members;
- optional-member advisory behavior;
- strict `readiness-report/v1` schema validation; and
- readiness rendering that preserves Evidence Continuity and Check conclusion authority.

The full `make validate` suite must pass before handoff.

## Runtime and live acceptance

The GitHub Check rendering is a runtime change and therefore requires deployment after
merge. A later non-destructive acceptance campaign must retain evidence for:

1. a registered reciprocal product moving through `READY`;
2. a controlled required-member obstacle producing precise `BLOCKED` remediation without
   permission expansion; and
3. correction of that obstacle returning the same product to `READY`, followed by normal
   Product Assessment.

Until those steps and evidence retention are complete, Phase 15 must not be labeled
`COMPLETE`.

