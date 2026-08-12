# IaaP Guard Planning Reports

## Purpose

IaaP Guard planning converts deterministic repository or product findings into evidence-traceable improvement work without turning Guard into a backlog-management or delivery-execution product.

Repository path:

```text
scan-result/v1
      ↓
planning/catalog.yaml
      ↓
Objective
      ↓
Key Results
      ↓
Epics mapped to Key Results
      ↓
Features
      ↓
Candidate User Stories
      ↓
Candidate Tasks
      ↓
planning-report/v1
```

Multi-repository product path:

```text
product-assessment/v1
      ↓
product finding / member evidence
      ↓
Objective
      ↓
Key Results
      ↓
Epics mapped to Key Results
      ↓
Features
      ↓
Candidate User Stories
      ↓
Candidate Tasks
      ↓
product-planning-report/v1
```

The planning layer does not change architecture verdicts, product conclusions, rule semantics, relationship semantics, or maturity scores. The assessment remains authoritative for what Guard observed; planning is advisory guidance for what a team could do next.

## Live product-planning proof

Phase 12 live acceptance demonstrated product-level planning against a real cross-repository `IAP-C001` incompatibility.

Both member repositories independently scored 100, but the federated product failed at 96 because the Backstage storefront's `region` constraints were broader than the canonical product contract.

Guard generated a product Improvement Plan containing:

- 1 Objective;
- 3 Key Results;
- 1 Epic;
- 1 Feature;
- 1 candidate User Story; and
- 4 candidate Tasks.

A targeted storefront pull request applied the smallest contract correction, after which the product revalidated at SUCCESS 100.

Canonical evidence: [`Phase 12 live federation acceptance`](https://github.com/SAABOLImpactVenture/ai-powered-infrastructure-as-a-product/blob/main/artifacts/phase-12/live-federation-acceptance.json).

## Product boundary

Guard may:

- translate deterministic repository or product findings into improvement objectives;
- generate measurable Key Results from current evidence baselines;
- group repeated findings under remediation Epics;
- map every Epic to one or more Key Results;
- propose Features;
- produce candidate User Stories;
- produce candidate Tasks;
- define acceptance evidence;
- preserve traceability to rule IDs, repository names, paths, lines, and deterministic evidence;
- emit Markdown and normalized JSON.

Guard does **not**:

- assign people;
- estimate capacity;
- manage sprints;
- sequence delivery;
- track work status;
- autonomously create issues;
- autonomously edit repositories;
- implement remediation;
- approve remediation;
- replace a delivery-management product.

The words **candidate story** and **candidate task** are deliberate. Guard proposes a planning starting point; accountable teams decide whether and how the work enters their delivery system.

## Deterministic hierarchy

A report uses this hierarchy:

```text
Assessment
  └── Objective
       ├── Key Result
       ├── Key Result
       └── Epic
            ├── maps to Key Result IDs
            ├── Guard rule + evidence
            └── Feature
                 └── Candidate User Story
                      ├── Acceptance Evidence
                      └── Candidate Tasks
```

The hierarchy is traceable in both directions:

```text
Engineering evidence
  → Guard finding
  → Epic
  → Key Result
  → Objective
```

and:

```text
Objective
  → Key Result
  → Epic
  → Feature
  → Candidate Story
  → Candidate Task
  → Guard evidence
```

For product scope, the evidence link also retains the member repository that caused or exposed the product finding.

## Key Result semantics

V1 creates KRs from metrics Guard can actually demonstrate.

When a dimension has a score, the report can create a coverage KR such as:

```text
Raise Consumer Boundary evidence coverage from 50 to 100.
```

Every impacted dimension can also receive a finding-removal KR such as:

```text
Reduce unresolved Consumer Boundary Guard findings from 3 to 0.
```

When blocking FAIL findings exist, Guard can add a blocking-remediation KR such as:

```text
Reduce blocking Consumer Boundary FAIL findings from 2 to 0.
```

Guard does not fabricate runtime outcomes it cannot observe. Developer NPS, Time-to-Provision, Internal Adoption Rate, Repeat Consumption Rate, and Exception/Escape Rate can become planning inputs when a future telemetry contract supplies trustworthy evidence for them.

## Planning catalog

`planning/catalog.yaml` is the versioned deterministic planning authority for V1. Each Guard rule maps to:

- an Epic title;
- an expected outcome;
- a Feature;
- a candidate User Story template;
- acceptance evidence; and
- candidate Tasks.

The planning catalog version is independent of the architecture rule-catalog version so planning guidance can evolve without silently changing Guard's architecture verdict semantics.

Current repository contract:

```text
planningCatalogVersion: iaap-planning/v0.1.0
schemaVersion: planning-report/v1
```

Multi-repository product planning emits:

```text
schemaVersion: product-planning-report/v1
```

## Repository CLI

Generate a human-readable repository improvement plan:

```bash
PYTHONPATH=src python3 -m iaap_guard.cli plan . \
  --repository example/platform \
  --revision 0123456789abcdef0123456789abcdef01234567
```

Generate normalized JSON:

```bash
PYTHONPATH=src python3 -m iaap_guard.cli plan . \
  --repository example/platform \
  --revision 0123456789abcdef0123456789abcdef01234567 \
  --format json
```

Write the report to a file with `--output`.

## Product CLI

When member `scan-result/v1` evidence already exists, generate a product-level plan with:

```bash
PYTHONPATH=src python3 -m iaap_guard.cli product-plan \
  .iaap/product.yaml \
  evidence/contracts.json \
  evidence/storefront.json \
  evidence/control-plane.json
```

The CLI aggregates supplied member evidence. The GitHub App performs the additional trusted member federation and relationship evaluation needed for live cross-repository `IAP-C001` evidence.

## GitHub App experience

When a deterministic repository scan produces WARNING or FAIL findings, the GitHub App can append a repository **Improvement Plan** to the existing `IaaP Guard / Architecture` Check.

When trusted multi-repository scope produces product findings, the product-aware runtime can append a **Product Improvement Plan** derived from `product-assessment/v1`.

The Check retains the underlying architecture and product evidence, then shows the Objective, measurable Key Results, Epics mapped to those KRs, Features, candidate User Stories, candidate Tasks, and source-evidence traceability.

When there are no findings, Guard does not invent planning work.

GitHub rendering is only an adapter over normalized planning contracts and does not change Guard's permissions or infrastructure authority.

## Interaction with Evidence Continuity

Planning and Evidence Continuity answer different questions:

```text
Evidence Continuity
  → Did Guard evidence materially change and is revalidation required?

Planning
  → Given a deterministic finding, what evidence-traceable improvement work could address it?
```

A `REVIEW REQUIRED` continuity signal is not automatically a backlog item, and a planning recommendation is not approval to change infrastructure.

## Future extension: existing OKRs

A later contract may allow a repository or registered product to provide existing OKRs, for example under `.iaap/okrs.yaml`. Guard should then map findings to existing Key Results when evidence supports the mapping and create **suggested** objectives only when no suitable strategic context exists.

That future extension must not let Guard invent organizational strategy or claim success for metrics it cannot observe.
