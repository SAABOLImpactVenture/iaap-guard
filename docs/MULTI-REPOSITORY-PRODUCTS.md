# Multi-repository products

IaaP Guard can assess repositories that collectively deliver one infrastructure product.

## Trust requirements

The triggering repository cannot expand live product scope from an untrusted pull-request change. Product membership is resolved from trusted default branches and requires reciprocal registration from each intended member.

Automatic V1 federation requires:

- the same GitHub owner;
- compatible repository visibility;
- App access to every required member;
- reciprocal product identity and membership;
- resolvable immutable default-branch revisions; and
- no more than the published V1 member limit.

Missing or incompatible required members produce `INCOMPLETE` evidence rather than silent omission.

## Output

The hosted Check may append member completeness, weakest-member score, relationship findings, and a bounded Product Improvement Plan. Product context remains advisory and does not silently change the triggering repository's deterministic Check conclusion.

Public product and assessment document shapes are available in `schemas/`. Federation, evaluation, and token-handling implementation is maintained privately.
