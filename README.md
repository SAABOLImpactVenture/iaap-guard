# IaaP Guard

> **IaaS is what you buy. Infrastructure-as-a-Product is what you build. IaaP Guard makes sure you keep building it that way.**

IaaP Guard is a GitHub-native architecture and product-governance system that evaluates whether infrastructure is actually being engineered as a product.

## Product architecture

The product is intentionally small: a deterministic, stateless repository/PR evaluator with a reusable local core. It does **not** provision infrastructure, connect to customer clouds or Kubernetes clusters, run Terraform/TFE, remediate changes, or compete with generic security scanners.

```text
Repository / PR files
        ↓
Component classifier
        ↓
Structured deterministic parsers
        ↓
Versioned IaaP rule catalog
        ↓
Normalized findings
        ↓
Coverage-based maturity score
        ↓
JSON + human-readable result
```

Adapters remain thin around the same core:

```text
IaaP Guard Core
   ├── CLI
   ├── GitHub Action     # Phase 9 dogfood
   └── GitHub App        # distribution after dogfood evidence
```

The adapter is not the product. The durable product IP is the system of IaaP product knowledge, rules, evidence, compatibility, and operating model.

## Deterministic core

The merged Phase 8 core implements:

- context classification before rule evaluation;
- safe YAML/JSON and bounded text loading without executing repository code;
- all 11 rules in `rules/catalog.yaml`;
- normalized `scan-result/v1` output;
- transparent `coverage/v1` scoring;
- human-readable and JSON CLI output;
- the frozen positive/negative fixture contract; and
- repeatability, schema, scoring, fixture-isolation, and non-execution tests.

Run the complete validation gate:

```bash
python3 -m pip install -r requirements-ci.txt
make validate
```

Run a local scan:

```bash
PYTHONPATH=src python3 -m iaap_guard.cli scan . \
  --repository example/platform-repo \
  --revision 0123456789abcdef0123456789abcdef01234567
```

Use `--format json` for the normalized machine-readable contract.

## Phase 9 GitHub Action

Phase 9 adds a thin composite Action for dogfooding the same deterministic engine inside a repository workflow.

Pin it to an immutable commit:

```yaml
permissions:
  contents: read

steps:
  - uses: actions/checkout@v7
  - uses: actions/setup-python@v7
    with:
      python-version: '3.12'
  - id: iaap-guard
    uses: SAABOLImpactVenture/iaap-guard@<40-character-commit-sha>
    with:
      fail-on-failure: 'false'
```

During dogfood, findings remain non-blocking until the repository baseline is reviewed. See `docs/GITHUB-ACTION.md` for the authority and evidence contract.

## V0 principles

- Product over tooling.
- Stable consumer contracts.
- Replaceable experience layer.
- Bounded intelligence.
- Deterministic governance.
- Human authorization.
- Evidence first.
- One authoritative reconciler.
- Least privilege.
- Context-aware analysis rather than naive keyword grep.
- Minimum effort first.

## Repository contents

- `docs/PRODUCT.md` — product definition and explicit V0 exclusions.
- `docs/ARCHITECTURE.md` — smallest useful core and adapter boundary.
- `docs/RULE-CATALOG.md` — V0 deterministic rule semantics.
- `docs/SCORING.md` — transparent coverage-based maturity model.
- `docs/CORE.md` — implemented deterministic engine contract and limitations.
- `docs/DOGFOOD.md` — Phase 9 six-repository evidence plan.
- `docs/GITHUB-ACTION.md` — Phase 9 Action adapter and authority boundary.
- `adr/` — architecture decisions for deterministic-first, context-aware analysis.
- `rules/catalog.yaml` — machine-readable V0 rule catalog.
- `schemas/scan-result.schema.json` — normalized result contract.
- `fixtures/` — positive and negative architecture cases.
- `src/iaap_guard/` — deterministic core and CLI.
- `tests/` — frozen fixture and engine-invariant tests.
- `action.yml` — thin GitHub Action dogfood adapter.

## Current status

**PHASE 8 — Deterministic Core: COMPLETE**  
**PHASE 9 — Dogfood POC: IN PROGRESS**

The current Phase 9 objective is to prove the Action and deterministic engine against the actual six-repository portfolio before building the GitHub App webhook/check-run runtime.
