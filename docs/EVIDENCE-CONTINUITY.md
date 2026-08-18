# Evidence Continuity

Evidence Continuity compares deterministic observations from the trusted pull-request base and immutable head revisions.

The hosted Check can report:

- **SUPPORTED** — no Guard-material rule or finding change was detected;
- **REVIEW REQUIRED** — a material change means prior evidence should be revalidated; or
- **NOT ESTABLISHED** — an appropriate trusted baseline could not be established.

Continuity evidence can include immutable revisions, product and scoring contract versions, rule-state transitions, introduced or resolved findings, and a deterministic evidence digest.

Evidence Continuity is advisory. It does not establish legal, institutional, security, compliance, exception, deployment, or risk-acceptance authority. Evidence continuity is not authorization continuity.

The public document shapes are retained in `schemas/`. Evaluation logic and regression tests are maintained privately.
