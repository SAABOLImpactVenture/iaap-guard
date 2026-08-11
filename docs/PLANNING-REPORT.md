# IaaP Guard Planning Report

## Purpose

The planning report converts deterministic IaaP Guard findings into an evidence-traceable improvement plan without turning Guard into a backlog-management or delivery-execution product.

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

The planning layer does not change the architecture verdict, rule semantics, or maturity score. The scan remains authoritative for what Guard observed; the planning report is advisory guidance for what a team could do next.

## Product boundary

Guard may:

- translate findings into improvement objectives;
- generate measurable Key Results from current evidence baselines;
- group repeated findings under remediation Epics;
- map every Epic to one or more Key Results;
- propose Features;
- produce candidate User Stories;
- produce candidate Tasks;
- define acceptance evidence;
- preserve traceability to rule IDs, repository paths, lines, and deterministic evidence;
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

## Key Result semantics

V1 creates KRs from metrics Guard can actually demonstrate.

When a dimension has a score, the report creates a coverage KR such as:

```text
Raise Consumer Boundary evidence coverage from 50 to 100.
```

Every impacted dimension also receives a finding-removal KR such as:

```text
Reduce unresolved Consumer Boundary Guard findings from 3 to 0.
```

When blocking FAIL findings exist, Guard adds a blocking-remediation KR such as:

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

Current contract:

```text
planningCatalogVersion: iaap-planning/v0.1.0
schemaVersion: planning-report/v1
```

## CLI

Generate a human-readable improvement plan:

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

## GitHub App target experience

The GitHub App should surface a compact planning section beneath deterministic findings so a team can move from architecture evidence to a planning conversation without leaving the pull request.

The canonical machine-readable report remains `planning-report/v1`. GitHub rendering is only an adapter over that contract.

## Future extension: existing OKRs

A later contract may allow a repository or registered product to provide existing OKRs, for example under `.iaap/okrs.yaml`. Guard should then map findings to existing Key Results when evidence supports the mapping and create **suggested** objectives only when no suitable strategic context exists.

That future extension must not let Guard invent organizational strategy or claim success for metrics it cannot observe.
