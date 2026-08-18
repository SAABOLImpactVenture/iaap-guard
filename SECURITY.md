# Security Policy

## Supported surface

Security fixes apply to the hosted IaaP Guard GitHub App and the current public contracts and documentation on `main`.

The former public composite Action is retired. Historical commits, tags, and proof-of-concept artifacts are not supported releases and do not receive current product or security updates.

## Reporting a vulnerability

Use GitHub Private Vulnerability Reporting through **Security → Advisories → Report a vulnerability**.

Do not disclose credentials, exploit details, private repository information, webhook payloads, installation tokens, cloud identifiers not already public, or sensitive reproduction material in a public issue or pull request.

If Private Vulnerability Reporting is unavailable, open a public issue containing no sensitive details and request a private communication path.

## Security boundary

Security-sensitive hosted components include webhook signature verification, short-lived installation-token use, immutable repository acquisition, Check Run publication, evidence integrity, and cloud deployment. Their implementation and internal regression tests are maintained privately.

The public contract intentionally excludes repository mutation, workflow administration, merge authority, customer-cloud credentials, provisioning, remediation, exception approval, and risk-acceptance authority.
