# IaaP Guard Scoring Model

Scoring model version: `coverage/v1`

## Goal

The maturity score must describe demonstrated control coverage, not encode arbitrary product opinions as hidden weights.

## Rule scoring

For applicable, scoring-enabled rules:

- `PASS` = satisfied.
- `WARNING` = unsatisfied.
- `FAIL` = unsatisfied.
- `NOT_APPLICABLE` = excluded.

There are no half-points in V0.

Experimental rules are excluded from scoring regardless of result.

## Dimensions

V0 uses these dimensions:

1. Product Abstraction
2. Consumer Boundary
3. Experience / Authority
4. Control-Plane Separation
5. Governance
6. Evidence Readiness

A dimension with zero applicable scoring rules is excluded from the overall score.

## Dimension score

```text
dimension score =
  passing applicable scoring rules
  --------------------------------
  all applicable scoring rules
  × 100
```

Scores are rounded to the nearest whole number for display, while normalized JSON may retain the exact numerator and denominator.

## Overall score

The overall score is the equal-weight arithmetic mean of applicable dimension scores.

This prevents a dimension with many low-level rules from dominating the product result simply because it contains more checks.

## Example

```text
Product Abstraction        100%  (2/2)
Consumer Boundary           67%  (2/3)
Experience / Authority     100%  (2/2)
Governance                  50%  (1/2)
Evidence Readiness           0%  (0/1)
Control-Plane Separation     N/A

Overall = mean(100, 67, 100, 50, 0) = 63
```

The score is evidence coverage, not a production-readiness certification.

## Important interpretation

A high score means the applicable V0 IaaP controls were demonstrably satisfied. It does **not** prove:

- security compliance;
- production readiness;
- cloud resource correctness;
- cost optimization;
- operational maturity outside the rule catalog;
- that the repository uses Crossplane, Backstage, Terraform, TFE, or any particular technology.

## Versioning

Every result must include:

- `ruleCatalogVersion`, currently `iaap-guard/v0.1.2`;
- `scoringModelVersion`, currently `coverage/v1`.

A result without both versions is not reproducible evidence.
