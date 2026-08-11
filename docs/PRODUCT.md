# IaaP Guard Product Contract

## Objective

Prove that a small GitHub-native evaluator can identify Infrastructure-as-a-Product architecture and governance problems **and preserve reconstructable evidence about how that evaluated state changes over time** before we invest in a persistent SaaS control plane.

The product now answers two related questions:

> **Is this infrastructure actually being designed, delivered, and governed as a product?**

and

> **When the observed product state changes, can we prove what Guard previously observed, what changed, and whether accountable revalidation is required?**

The second question is intentionally narrower than authorization. IaaP Guard can establish evidence continuity within its deterministic scope; it cannot establish legal, institutional, deployment, exception, risk-acceptance, or disposition authority.

## Product outcomes

IaaP Guard should help a team achieve five outcomes:

1. **Detect product-boundary drift early.** Infrastructure implementation details, execution authority, lifecycle choices, or governance gaps should be visible before they silently become part of the consumer contract.
2. **Produce explainable evidence.** Every result should identify the rule, evaluated artifact/context, deterministic evidence, ruleset/scoring version, and immutable revision where available.
3. **Make change reconstructable.** A later evaluation should be comparable to a prior trustworthy Guard state so rule-state transitions and finding-evidence changes can be reconstructed.
4. **Signal when prior evidence should be revalidated.** Material Guard-observed changes should produce a bounded `review_required` disposition instead of silently treating yesterday's evidence as current.
5. **Preserve accountable human governance.** Guard must remain an evidence and decision-support product, not an authorization, approval, remediation, or infrastructure-execution authority.

## Smallest useful product

IaaP Guard evaluates repository and pull-request artifacts using deterministic, context-aware rules. It classifies relevant components, evaluates applicable controls, returns normalized findings, calculates a transparent maturity score, and can emit a versioned evidence manifest that compares prior and current Guard-observed states.

The product is useful when it can distinguish between an implementation technology being used legitimately behind a product boundary and that same technology leaking into a consumer contract or gaining inappropriate authority. It becomes more useful when it can also distinguish **technical executability** from **continued evidentiary support for the previously observed governance state**.

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

These remain point-in-time architecture semantics.

## Evidence Continuity semantics

Evidence Continuity compares a prior trustworthy Guard result with the current Guard result and records what changed within Guard's deterministic scope.

- **supported** — no Guard-material rule/finding change was detected between the baseline and current evidence.
- **review_required** — a Guard-material rule/finding change was detected and the prior evidence should not be silently treated as still applicable.
- **not_established** — a suitable baseline was not available or continuity could not be established.

The evidence manifest may include immutable revisions, ruleset/scoring versions, rule-state transitions, introduced/resolved finding evidence, deterministic evidence digests, materiality, and bounded disposition.

**Evidence continuity is not authorization continuity.** `supported` is not a statement that an action is legally, institutionally, operationally, security, compliance, deployment, or exception-authorized. `review_required` does not itself decide who has disposition authority or what decision that authority must make.

## GitHub PR baseline rule

For the GitHub App, an IaaP-relevant pull request must not choose its own continuity baseline. The technical baseline comes from the immutable PR-base SHA supplied by GitHub pull-request state; the current state comes from the immutable PR-head SHA.

This keeps the baseline outside the control of the proposed change while preserving the existing narrow GitHub App permissions and stateless runtime model.

## Explicit exclusions

IaaP Guard does not provide:

- cloud provisioning or remediation;
- cloud, Kubernetes, Terraform/TFE or customer credential access;
- Terraform state inspection;
- secret, CVE or generic IaC vulnerability scanning;
- NIST, FedRAMP, SOC 2 or other compliance determinations;
- legal or institutional authorization determinations;
- autonomous disposition of changed evidence;
- AI-generated scoring verdicts;
- autonomous code changes, pull requests, approvals or merges;
- branch-protection or ruleset administration;
- organization-wide dashboards or historical trend storage;
- Marketplace billing;
- live reconciliation validation;
- a claim that Terraform or TFE has no legitimate role.

## Authority model

IaaP Guard observes repository artifacts, compares Guard evidence, and reports architecture/evidence findings. It receives no infrastructure or approval authority.

```text
GitHub artifacts / immutable revisions
      ↓ read
IaaP Guard
      ↓ deterministic findings + evidence continuity
GitHub Check / local output
      ↓
Accountable human or governed process decides disposition
```

Guard must never turn an architecture-analysis and evidence product into another infrastructure execution path or a machine authorization oracle.

## Commercial learning goal

IaaP Guard is successful when teams find the IaaP-specific findings, reconstructable evidence, and continuity signals useful enough to install, repeatedly run, discuss, request broader policy/evidence capabilities, or incorporate into their review process.

The first commercial signal is product pull around **architecture evidence + evidence continuity**, not hosted-system complexity.
