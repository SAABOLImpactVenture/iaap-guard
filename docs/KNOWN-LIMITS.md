# V1 Known Limits

IaaP Guard V1 is bounded decision support, not a universal infrastructure scanner.

## Analysis limits

- Supported full-scan suffixes: `.yaml`, `.yml`, `.json`, `.tf`, `.tofu`,
  `.hcl`, `.md`, `.py`, and `.sh`.
- Compressed repository archive: 25 MB maximum.
- Archive members: 20,000 maximum.
- Extracted regular-file bytes: 100 MB maximum.
- Analyzed file: 1 MB maximum.
- Cross-repository relationship bundle: 20 MB maximum.
- Registered product members: 12 maximum.
- Automatic V1 federation is same-owner and same-visibility only.
- Reciprocal trusted default-branch manifests and App access are required for every
  federated member.

Required product evidence that cannot be obtained within supported bounds fails closed
or becomes `INCOMPLETE`. Files with unsupported suffixes are not analyzed; a pull request
changing only unsupported suffixes receives the documented successful `No relevant
changes` result.

## Interpretation limits

A warning in a standalone infrastructure module can be context-dependent. V1 evaluates
Infrastructure-as-a-Product evidence; it does not claim that every Terraform module,
workflow, or repository must itself be a complete product.

Scores measure coverage of applicable Guard rules. They are not security, compliance,
reliability, production-readiness, legal, risk, or deployment authorization scores.

## Adapter limits

The GitHub App is stateless and publicly reachable through a reference AWS Lambda
deployment. It requires supported pull-request events, a valid webhook signature, App
access to required repositories, and inputs within archive limits. Hosting availability
is not part of the deterministic contract.

GitHub Enterprise Server, enterprise-specific policy combinations, restricted network
paths, nonstandard repository content models, and deployment-specific scale are not
universally qualified. Their expected behavior and required adoption evidence are defined
in [Environment compatibility Q&A](ENVIRONMENT-COMPATIBILITY-QA.md) and
[Production readiness and operations Q&A](PRODUCTION-READINESS-QA.md).

## Explicit exclusions

The complete authoritative exclusion list is
[`PRODUCT.md#explicit-exclusions`](PRODUCT.md#explicit-exclusions). In particular, V1
does not ingest organizational OKRs, manage enterprise strategy or team work, execute
infrastructure, hold customer infrastructure credentials, mutate repositories,
automatically remediate or authorize, provide persistent customer analytics, federate
automatically across organizations, bill through Marketplace, certify compliance, or
claim production readiness.
