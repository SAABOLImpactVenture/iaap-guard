# Support Policy

## Supported release

IaaP Guard `1.0.x` is the supported V1 line. The repository's latest V1 patch release
contains the supported source, GitHub Action, schemas, rules, and operator guidance.

## Support channels

Use GitHub Issues for reproducible defects, security-neutral questions, documentation
problems, and compatibility reports. Include the Guard version, immutable repository
revision, adapter used, sanitized result, and reproduction steps.

Report vulnerabilities privately according to [`SECURITY.md`](../SECURITY.md). Do not
place credentials, private keys, webhook secrets, installation tokens, private
repository contents, or exploitable vulnerability details in a public issue.

## Service level

V1 is an open-source, best-effort product. No uptime, response-time, remediation-time, or
professional-services commitment is implied. The hosted public App is a replaceable beta
distribution adapter and may have maintenance windows or capacity constraints.

## Supported scope

Support covers deterministic behavior inside the frozen V1 contracts, documented
installation and operation, and the reference GitHub Action and App adapters. It does
not cover customer infrastructure operation, Terraform module correctness, cloud
account administration, organizational policy decisions, compliance certification,
authorization decisions, or work management.

## Maintenance

Compatible security, dependency, defect, documentation, and operational fixes may be
released as V1 patches. Backward-incompatible changes require a separately versioned
successor contract and migration guidance.
