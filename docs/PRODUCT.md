# IaaP Guard V0 Product Contract

## Objective

Prove that a small GitHub-native evaluator can identify Infrastructure-as-a-Product architecture and governance problems before we invest in a persistent SaaS control plane.

The unique product question is:

> **Is this infrastructure actually being designed, delivered, and governed as a product?**

## Smallest useful product

IaaP Guard V0 evaluates repository and pull-request artifacts using deterministic, context-aware rules. It classifies relevant components, evaluates applicable controls, returns normalized findings, and calculates a transparent maturity score.

V0 is useful when it can distinguish between an implementation technology being used legitimately behind a product boundary and that same technology leaking into a consumer contract or gaining inappropriate authority.

## Initial supported component contexts

1. **consumer-contract** — product APIs, XRD/CRD schemas, JSON Schema, OpenAPI or equivalent request contracts.
2. **experience** — Backstage templates, forms, order schemas, CLIs, portals or comparable consumer surfaces.
3. **ai-authority** — agent configuration, runtime policy, tool allow/deny lists and approval behavior.
4. **control-plane-implementation** — Crossplane Compositions/provider resources and Terraform/OpenTofu implementation artifacts.
5. **bootstrap** — minimal trusted control-plane installation and seed guardrails.
6. **evidence** — tests, CI, compatibility checks, status/evidence schemas and teardown controls.
7. **documentation-fixture** — prose, examples and intentionally bad test cases that must not be mistaken for live consumer surfaces.

## Initial repository support priority

1. Infrastructure product repositories.
2. Experience/storefront repositories.
3. AI infrastructure-assistance repositories.
4. Infrastructure implementation repositories.
5. Evidence/integration repositories.
6. Bootstrap repositories.

Plain application repositories should normally receive mostly `NOT_APPLICABLE`, not an artificially low IaaP score.

## Result semantics

- **PASS** — an applicable deterministic control has positive evidence.
- **WARNING** — a non-blocking product/evidence gap exists or a risk requires human review.
- **FAIL** — direct deterministic evidence violates a non-negotiable IaaP product or authority boundary.
- **NOT_APPLICABLE** — the capability is not present or the rule does not apply; excluded from scoring.

## Explicit V0 exclusions

V0 does not provide:

- cloud provisioning or remediation;
- cloud, Kubernetes, Terraform/TFE or customer credential access;
- Terraform state inspection;
- secret, CVE or generic IaC vulnerability scanning;
- NIST, FedRAMP, SOC 2 or other compliance mappings;
- AI-generated scoring verdicts;
- autonomous code changes, pull requests, approvals or merges;
- branch-protection or ruleset administration;
- organization-wide dashboards or historical trend storage;
- Marketplace billing;
- live reconciliation validation;
- a claim that Terraform or TFE has no legitimate role.

## Authority model

IaaP Guard observes repository artifacts and reports architecture findings. It receives no infrastructure authority.

```text
GitHub artifacts
      ↓ read
IaaP Guard
      ↓ findings
GitHub Check / local output
```

Guard must never turn an architecture-analysis product into another infrastructure execution path.

## Commercial learning goal

V0 is successful when teams find the IaaP-specific findings useful enough to install, repeatedly run, discuss, or request broader policy/evidence capabilities. The first commercial signal is product pull, not hosted-system complexity.
