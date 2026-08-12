# IaaP Guard Product Contract

## Objective

Prove that a small GitHub-native evaluator can identify Infrastructure-as-a-Product architecture and governance problems, connect evidence across explicitly registered repositories, and preserve reconstructable evidence about how that evaluated state changes over time before investing in a persistent SaaS control plane.

The product now answers three related questions:

> **Is this infrastructure actually being designed, delivered, and governed as a product?**

> **If the product spans repositories, do the registered members still form one coherent consumer/product contract?**

> **When the observed product state changes, can we prove what Guard previously observed, what changed, and whether accountable revalidation is required?**

The temporal question is intentionally narrower than authorization. IaaP Guard can establish evidence continuity within its deterministic scope; it cannot establish legal, institutional, deployment, exception, risk-acceptance, compliance, or disposition authority.

## Product outcomes

IaaP Guard should help a team achieve seven outcomes:

1. **Detect product-boundary drift early.** Infrastructure implementation details, execution authority, lifecycle choices, or governance gaps should be visible before they silently become part of the consumer contract.
2. **Produce explainable evidence.** Every result should identify the rule, evaluated artifact/context, deterministic evidence, ruleset/scoring version, and immutable revision where available.
3. **Treat a logical product as larger than one repository.** A storefront, product contract, control plane, governance policy, implementation, and evidence repository can remain independently owned without becoming invisible to product-level architecture review.
4. **Detect cross-repository relationship drift.** Individually healthy repositories must not be allowed to hide an incompatible product boundary between them.
5. **Make change reconstructable.** A later evaluation should be comparable to a prior trustworthy Guard state so rule-state transitions and finding-evidence changes can be reconstructed.
6. **Signal when prior evidence should be revalidated.** Material Guard-observed changes should produce a bounded `review_required` disposition instead of silently treating yesterday's evidence as current.
7. **Preserve accountable human governance.** Guard must remain an evidence and decision-support product, not an authorization, approval, remediation, work-assignment, or infrastructure-execution authority.

## Proven product outcomes

### Phase 12 — multi-repository product scope

The live acceptance campaign registered the **Cloud Foundation Environment** as a real two-repository product using reciprocal trusted default-branch membership.

The proof established an important product behavior:

```text
Repository A: PASS 100
Repository B: PASS 100
Cross-repository contract relationship: incompatible
Product: FAILURE 96
```

Trusted federation identified `IAP-C001` because the Backstage storefront allowed a broader `region` shape than the canonical product contract. Guard then generated an evidence-backed product Improvement Plan. A targeted storefront correction restored the logical product to **SUCCESS 100**, and the primary member independently revalidated the complete 2/2 product at **SUCCESS 100**.

This proves that repository health and product relationship health are distinct signals rather than different labels for the same scan.

Canonical evidence: [`Phase 12 live federation acceptance`](https://github.com/SAABOLImpactVenture/ai-powered-infrastructure-as-a-product/blob/main/artifacts/phase-12/live-federation-acceptance.json).

### Phase 14 — PR-base Evidence Continuity

The deployed App was exercised on a fresh pull request from current main.

The same PR first produced:

```text
Architecture: PASS 100
Evidence Continuity: SUPPORTED
Guard materiality: no_guard_material_change_detected
```

After a controlled Guard-material change, the same PR produced:

```text
Architecture: WARNING 67
Finding: IAP-P004
Evidence Continuity: REVIEW REQUIRED
Guard materiality: guard_material_change_detected
Disposition: human_review_required
```

The GitHub Check conclusion remained owned by the repository architecture result, preserving the advisory continuity boundary.

Canonical evidence: [`Phase 14 live acceptance`](https://github.com/SAABOLImpactVenture/ai-powered-infrastructure-as-a-product/blob/main/artifacts/phase-14/live-acceptance.json).

## Smallest useful product

IaaP Guard evaluates repository and pull-request artifacts using deterministic, context-aware rules. It classifies relevant components, evaluates applicable controls, returns normalized findings, calculates a transparent maturity score, and can emit a versioned evidence manifest that compares prior and current Guard-observed states.

For registered multi-repository products, it can also aggregate member evidence into `product-assessment/v1`, evaluate explicitly bounded cross-repository relationships, and generate `product-planning-report/v1`.

The product is useful when it can distinguish between an implementation technology being used legitimately behind a product boundary and that same technology leaking into a consumer contract or gaining inappropriate authority. It becomes more useful when it can also distinguish:

- repository health from product-relationship health; and
- technical executability from continued evidentiary support for a previously observed governance state.

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

## Repository result semantics

- **PASS** — an applicable deterministic control has positive evidence.
- **WARNING** — a non-blocking product/evidence gap exists or a risk requires human review.
- **FAIL** — direct deterministic evidence violates a non-negotiable IaaP product or authority boundary.
- **NOT_APPLICABLE** — the capability is not present or the rule does not apply; excluded from scoring.

These remain point-in-time architecture semantics.

## Product result semantics

A registered product produces a separate product assessment.

- **SUCCESS** — required member evidence is complete and neither member nor relationship evidence fails the product.
- **FAILURE** — a member or explicitly supported product relationship fails.
- **INCOMPLETE** — Guard cannot establish complete required evidence or cannot complete the bounded relationship evaluation.

The numeric product score summarizes demonstrated coverage. It never averages away a member or relationship failure.

Product scope is advisory in V1. The triggering repository still owns the GitHub Check conclusion.

## Evidence Continuity semantics

Evidence Continuity compares a prior trustworthy Guard result with the current Guard result and records what changed within Guard's deterministic scope.

- **supported** — no Guard-material rule/finding change was detected between baseline and current evidence.
- **review_required** — a Guard-material rule/finding change was detected and prior evidence should not be silently treated as still applicable.
- **not_established** — a suitable baseline was not available or continuity could not be established.

The evidence manifest may include immutable revisions, ruleset/scoring versions, rule-state transitions, introduced/resolved finding evidence, deterministic evidence digests, materiality, and bounded disposition.

**Evidence continuity is not authorization continuity.** `supported` is not a statement that an action is legally, institutionally, operationally, security, compliance, deployment, or exception-authorized. `review_required` does not itself decide who has disposition authority or what decision that authority must make.

## GitHub PR baseline rule

For the GitHub App, an IaaP-relevant pull request must not choose its own continuity baseline. The technical baseline comes from the immutable PR-base SHA supplied by GitHub pull-request state; the current state comes from the immutable PR-head SHA.

This keeps the baseline outside the control of the proposed change while preserving the existing narrow GitHub App permissions and stateless runtime model.

## Multi-repository trust rule

A pull request also must not be allowed to unilaterally enlarge Guard's related-repository read scope.

For automatic V1 federation:

- trusted membership comes from `.iaap/product.yaml` on the triggering repository's default branch;
- every related repository must reciprocally declare the same normalized product identity and membership on its own default branch;
- members must be under the same GitHub owner and visibility;
- IaaP Guard must be installed with access to each required member; and
- related repository tokens are short-lived, repository-specific, and `contents:read` only.

Missing required evidence produces `INCOMPLETE` rather than silent omission.

See [`ADOPTION-PREREQUISITES.md`](ADOPTION-PREREQUISITES.md) for the practical adoption and troubleshooting path.

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
- portfolio discovery by crawling unregistered repositories;
- cross-organization V1 federation;
- Marketplace billing;
- live reconciliation validation;
- a claim that Terraform or TFE has no legitimate role.

## Authority model

IaaP Guard observes repository artifacts, compares Guard evidence, connects only explicitly trusted product members, and reports architecture/product/evidence findings. It receives no infrastructure or approval authority.

```text
GitHub artifacts / immutable revisions
      ↓ read
IaaP Guard
      ↓ deterministic repository findings
      ↓ optional trusted product assessment
      ↓ evidence continuity
GitHub Check / local output
      ↓
Accountable human or governed process decides disposition
```

Guard must never turn an architecture-analysis and evidence product into another infrastructure execution path or a machine authorization oracle.

## Commercial learning goal

IaaP Guard is successful when teams find the IaaP-specific findings, reconstructable evidence, product relationship signals, and continuity signals useful enough to install, repeatedly run, discuss, request broader policy/evidence capabilities, or incorporate into their review process.

The strongest current product signal is **architecture evidence + multi-repository product coherence + evidence continuity**, not hosted-system complexity.
