# Adoption prerequisites

Before relying on IaaP Guard:

1. Install the [hosted GitHub App](https://github.com/apps/iaap-guard) for the intended repositories.
2. Grant only metadata read, contents read, pull-request read, and checks read/write.
3. Open a pull request that changes at least one supported file type: YAML, JSON, Terraform/HCL, Markdown, Python, or shell.
4. Confirm `IaaP Guard / Architecture` appears on the current pull-request head.
5. Review the Check as deterministic evidence, not as legal, security, exception, deployment, or risk-acceptance authorization.

For multi-repository products, every intended member must be accessible to the same App installation and must publish reciprocal trusted product membership on its default branch. Missing, inaccessible, visibility-incompatible, or non-reciprocal members produce bounded incomplete evidence rather than silent omission.

The former composite Action and local public CLI are retired. Historical pinned revisions are unsupported.

See [known limits](KNOWN-LIMITS.md), [multi-repository products](MULTI-REPOSITORY-PRODUCTS.md), and [support](SUPPORT.md).
