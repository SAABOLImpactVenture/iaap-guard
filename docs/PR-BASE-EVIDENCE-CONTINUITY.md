# PR-Base Evidence Continuity

Phase 14 integrates the Phase 13 `evidence-manifest/v1` contract into the GitHub App pull-request path.

## Purpose

A point-in-time architecture result answers what IaaP Guard sees at the PR head. Phase 14 adds a second question:

> How does the Guard evidence at this PR head differ from the Guard evidence at the pull request's base revision?

The comparison is automatic for IaaP-relevant pull requests and is published inside the existing **IaaP Guard / Architecture** Check.

## Runtime path

```text
GitHub PR event
      ↓
existing signature + installation-token boundary
      ↓
PR-head deterministic scan
      ↓
PR-base immutable SHA from GitHub pull-request state
      ↓
PR-base deterministic scan
      ↓
build_evidence_manifest(head, base)
      ↓
SUPPORTED / REVIEW REQUIRED / NOT ESTABLISHED
      ↓
existing Architecture Check + advisory Evidence Continuity section
```

The PR head does not choose the baseline. For normal pull-request events, the baseline SHA comes from `pull_request.base.sha` in the GitHub event. For Check rerequests, IaaP Guard reads the current pull-request object and resolves its base SHA through the existing repository-scoped installation token.

## Check semantics

Evidence continuity is advisory in Phase 14.

The existing deterministic repository scan still owns the GitHub Check conclusion:

- repository `success` remains Check `success`;
- repository `neutral` remains Check `neutral`;
- repository `failure` remains Check `failure`.

A continuity result of `review_required` is displayed prominently but does **not** silently convert a repository PASS into a blocking failure. This preserves the stable consumer contract while the organization decides how evidence-review disposition should be wired into human governance.

The Check includes:

- PR-base revision;
- evidence-continuity status;
- Guard materiality;
- bounded disposition;
- rule-state transition count;
- finding-evidence introduced/resolved counts;
- evidence digest; and
- the explicit non-authorization boundary.

## Why PR base is the baseline

The PR base is useful because it is:

- supplied by GitHub's pull-request state rather than untrusted repository content;
- an immutable commit SHA;
- readable with the same repository-scoped `contents:read` authority already used by Guard;
- available without introducing a database; and
- directly relevant to the change under review.

It is **not** automatically a legal, risk, security, or institutional approval baseline. It is a technical Guard-evidence baseline only.

## Interaction with product scope

The product-aware runtime may replace the initial repository Check output to append multi-repository product context. Phase 14 carries the evidence manifest forward internally so that the final Check retains both layers:

```text
Repository architecture result
        +
PR-base evidence continuity
        +
registered multi-repository product context (when present)
```

Repository scan semantics continue to own the Check conclusion. Both evidence continuity and product scope are advisory layers.

## No new permissions

Phase 14 requires no GitHub App permission expansion.

The existing V0 authority remains:

- Metadata: read;
- Contents: read;
- Pull requests: read;
- Checks: write.

No repository content writes, workflow administration, cloud credentials, Kubernetes credentials, Terraform/TFE credentials, PATs, or persistent customer database are introduced.

## Boundary

**Evidence continuity is not authorization continuity.**

A `supported` result means that IaaP Guard re-evaluated the PR head and the PR base without detecting a material change in its own rule/finding evidence model. It does not mean that the action is approved, compliant, safe, deployable, legally authorized, risk accepted, or covered by a still-valid exception.

A `review_required` result means Guard evidence materially changed and accountable review is warranted. IaaP Guard does not decide who possesses disposition authority or what the disposition must be.
