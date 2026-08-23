# Adoption readiness

A repository is ready for hosted IaaP Guard evaluation when:

- the App is installed for the repository;
- a current pull request changes a supported file type;
- the App can read immutable base and head repository snapshots within published limits; and
- `IaaP Guard / Architecture` can be published on the head revision.

A multi-repository product additionally requires same-owner and visibility-compatible member access, reciprocal default-branch product registration, resolvable immutable member revisions, and compliance with the published V1 member limit.

Readiness is reported through the hosted Check. It is advisory and does not grant deployment, exception, security, compliance, or risk-acceptance authority.

Meeting these prerequisites establishes eligibility for evaluation, not universal
environment compatibility or production readiness. Before production use, qualify the
intended GitHub and network configuration through
[Environment compatibility Q&A](ENVIRONMENT-COMPATIBILITY-QA.md) and satisfy every
applicable blocking gate in
[Production readiness and operations Q&A](PRODUCTION-READINESS-QA.md).
