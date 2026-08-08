# IaaP Guard GitHub Action — Phase 9 Dogfood Adapter

## Purpose

The Phase 9 GitHub Action is a thin distribution adapter around the deterministic IaaP Guard core. It exists to dogfood the same scanner inside GitHub Actions without introducing a hosted service, database, cloud credentials, Kubernetes credentials, Terraform/TFE authority, or repository write authority.

The adapter does not redefine rule semantics or scoring.

## Usage

Pin the action to an immutable commit:

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

During dogfood, `fail-on-failure` remains `false` so findings are evidence rather than an unexplained merge blocker. Once a repository baseline is accepted, that repository may deliberately choose to make deterministic `FAIL` findings blocking.

## Inputs

- `target` — repository-relative path to scan; default `.`.
- `output` — repository-relative normalized result path; default `artifacts/iaap-guard/scan-result.json`.
- `fail-on-failure` — when `true`, return a failing action step if the Guard conclusion is `failure`; default `false`.

The adapter rejects target/output paths that escape `GITHUB_WORKSPACE`.

## Outputs

- `conclusion` — `success`, `neutral`, or `failure`.
- `score` — coverage score when applicable.
- `result-path` — repository-relative result file path.
- `findings` — number of WARNING/FAIL findings.

## Evidence behavior

The action records:

- exact repository identity from `GITHUB_REPOSITORY`;
- exact immutable analyzed revision from `GITHUB_SHA`;
- Git ref when available;
- exact Guard ruleset and scoring model versions;
- deterministic findings and scores.

The caller may upload the JSON result as a GitHub Actions artifact. IaaP Guard itself does this during the Phase 9 self-dogfood gate.

## Authority boundary

The action requires only a checked-out repository. The recommended workflow permission is:

```yaml
permissions:
  contents: read
```

It does not need:

- `contents: write`;
- pull-request write access;
- checks write access;
- cloud credentials;
- Kubernetes credentials;
- Terraform/TFE credentials;
- AI/model credentials.

A future GitHub App adapter may use Checks write permission to create a purpose-built check surface. That is explicitly outside this Phase 9 Action adapter.

## Internal-repository distribution experiment

`iaap-guard` is currently internal. Cross-repository Action consumption therefore depends on GitHub repository/organization Action-access settings. Phase 9 will test that behavior against one bounded internal portfolio repository before adding workflows to the rest of the portfolio.

If GitHub denies cross-repository Action access, do not solve it by introducing a broad PAT or duplicating Guard source into every repository. Treat the access failure as evidence and choose the smallest governed distribution adjustment.
