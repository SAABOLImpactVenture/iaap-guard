# IaaP Guard hosted GitHub App

## Install

Install IaaP Guard from [github.com/apps/iaap-guard](https://github.com/apps/iaap-guard) and grant access only to the repositories you want evaluated.

The App uses:

| Permission | Access |
|---|---|
| Metadata | Read |
| Contents | Read |
| Pull requests | Read |
| Checks | Read and write |

It subscribes to supported pull-request events and bounded check-run rerequests. It does not request repository content-write, workflow administration, merge, deployment, secrets, member-management, provisioning, or remediation authority.

## Expected output

For supported pull-request changes, the App publishes `IaaP Guard / Architecture`. The Check may include:

- architecture conclusion, score, and findings;
- immutable base and head revisions;
- advisory Evidence Continuity;
- trusted multi-repository Product Assessment and Improvement Plan; and
- bounded next actions.

The repository-owned deterministic result controls the Check conclusion. Evidence Continuity and product context remain advisory and do not confer authorization.

## Troubleshooting

1. Confirm the App is installed for the triggering repository.
2. Confirm the pull request changed a supported file type.
3. Confirm the Check appears on the current head revision.
4. Review [adoption prerequisites](ADOPTION-PREREQUISITES.md) and [known limits](KNOWN-LIMITS.md).
5. Follow [support guidance](SUPPORT.md) without posting credentials or sensitive repository content publicly.

## Operator boundary

Hosting implementation, signing-secret handling, installation-token exchange, deterministic rule execution, cloud deployment, and internal validation are maintained in a protected private repository. This public repository does not contain or deploy the hosted runtime.
