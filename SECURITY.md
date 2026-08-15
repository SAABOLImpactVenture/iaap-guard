# Security Policy

## Supported versions

IaaP Guard is currently a beta product. Security fixes are applied to the
current `main` branch and the actively deployed beta runtime.

Older commits, experimental branches, and historical proof-of-concept
artifacts should not be treated as supported releases.

## Reporting a vulnerability

Do not disclose suspected vulnerabilities, credentials, exploit details,
or sensitive reproduction information in a public issue or pull request.

Use GitHub Private Vulnerability Reporting when available:

**Security -> Advisories -> Report a vulnerability**

If private vulnerability reporting is temporarily unavailable, open a
public issue containing no exploit details and request a private
communication path.

## Security-sensitive scope

Security-sensitive components include:

- GitHub App authentication and webhook verification
- installation-token creation and use
- repository and multi-repository evidence acquisition
- Check Run publication
- GitHub Actions workflows
- AWS Lambda deployment and GitHub OIDC federation
- evidence integrity and immutable-revision handling
- trust-boundary and product-membership evaluation

IaaP Guard intentionally does not require customer cloud credentials,
repository content-write permission, workflow administration permission,
merge authority, provisioning authority, remediation authority, or
deployment authority. It does not ingest organizational OKRs, manage delivery
work, or make security, compliance, exception, or risk-acceptance decisions.

These security-specific statements inherit the canonical
[V1 explicit exclusions](docs/PRODUCT.md#explicit-exclusions) and do not expand
the product boundary.

## Disclosure

Please allow the maintainers an opportunity to investigate and remediate
a reported vulnerability before public disclosure.
