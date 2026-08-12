# PR-Base Evidence Continuity

## Status

**Phase 14 — COMPLETE**

PR-base Evidence Continuity is integrated into the GitHub App and live-proven in the deployed runtime.

Canonical evidence: [`Phase 14 live acceptance`](https://github.com/SAABOLImpactVenture/ai-powered-infrastructure-as-a-product/blob/main/artifacts/phase-14/live-acceptance.json).

## Purpose

A point-in-time architecture result answers what IaaP Guard sees at the PR head. PR-base Evidence Continuity adds a second question:

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

The PR head does not choose the baseline.

For normal pull-request events, the baseline SHA comes from `pull_request.base.sha` in the GitHub event. For Check rerequests, IaaP Guard reads the current pull-request object and resolves its base SHA through the existing repository-scoped installation token.

## Check semantics

Evidence Continuity is advisory.

The existing deterministic repository scan still owns the GitHub Check conclusion:

- repository `success` remains Check `success`;
- repository `neutral` remains Check `neutral`;
- repository `failure` remains Check `failure`.

A continuity result of `review_required` is displayed prominently but does **not** silently convert a repository PASS into a blocking failure. This preserves the stable consumer contract while the organization decides how evidence-review disposition should be wired into human governance.

The Check can include:

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

It is **not** automatically a legal, risk, security, compliance, exception, or institutional approval baseline. It is a technical Guard-evidence baseline only.

## Live acceptance

Phase 14 was closed with a fresh disposable pull request on `SAABOLImpactVenture/ai-powered-infrastructure-as-a-product`.

The PR used base revision:

```text
7ae95c9c384dfeeabb7246f07f3f2d6098a7ed18
```

### Case 1 — non-Guard-material change

Revision:

```text
f1d438b350e5b43cbeb5180813f2c37c50829e5f
```

Observed result:

```text
Architecture: PASS
Score: 100
Findings: 0
Evidence Continuity: SUPPORTED
Guard materiality: no_guard_material_change_detected
Disposition: no_additional_guard_review
Rule-state transitions: 0
Findings introduced: 0
Findings resolved: 0
```

### Case 2 — controlled Guard-material change

Revision:

```text
2fb81a670277966593f3fcbb5c6871fbfd2aca32
```

Observed result:

```text
Architecture: WARNING
Score: 67
Finding: IAP-P004
Evidence Continuity: REVIEW REQUIRED
Guard materiality: guard_material_change_detected
Disposition: human_review_required
Rule-state transitions: 4
Findings introduced: 1
Findings resolved: 0
```

The same pull request therefore proved the required transition from `SUPPORTED` to `REVIEW REQUIRED` in the deployed App.

The proof PR was closed unmerged. A manual rerequest was optional and was not required to satisfy the acceptance contract because immutable revision and Check Run evidence had already been captured.

## Interaction with product scope

The product-aware runtime may rewrite/enrich the initial repository Check output to append multi-repository product context. The Evidence Continuity manifest is carried forward so the final Check retains all applicable layers:

```text
Repository architecture result
        +
PR-base Evidence Continuity
        +
registered multi-repository Product Assessment
        +
Product Improvement Plan when needed
```

Repository scan semantics continue to own the Check conclusion. Both Evidence Continuity and product scope are advisory layers in V1.

Phase 12 live acceptance separately proved trusted federation, a real `IAP-C001` relationship failure, product planning, targeted remediation, and final Product SUCCESS 100.

See [`MULTI-REPOSITORY-PRODUCTS.md`](MULTI-REPOSITORY-PRODUCTS.md).

## No new permissions

Phase 14 required no GitHub App permission expansion.

The authority remains:

- Metadata: read;
- Contents: read;
- Pull requests: read;
- Checks: write.

No repository content writes, workflow administration, cloud credentials, Kubernetes credentials, Terraform/TFE credentials, PATs, or persistent customer database are introduced.

## Adoption and troubleshooting

A user does not need to configure a separate continuity database or choose a baseline.

If Evidence Continuity does not appear or becomes `NOT ESTABLISHED`, diagnose the GitHub/App/repository path before adding authority:

- confirm the App Check is being delivered;
- confirm the PR action is handled by the runtime;
- confirm a supported analysis suffix changed when a full scan is expected;
- confirm the PR base/head revisions are available from GitHub; and
- confirm both snapshots fit within current beta bounds.

See [`ADOPTION-PREREQUISITES.md`](ADOPTION-PREREQUISITES.md).

## Boundary

**Evidence continuity is not authorization continuity.**

A `supported` result means that IaaP Guard re-evaluated the PR head and PR base without detecting a material change in its own rule/finding evidence model. It does not mean that the action is approved, compliant, safe, deployable, legally authorized, risk accepted, or covered by a still-valid exception.

A `review_required` result means Guard evidence materially changed and accountable review is warranted. IaaP Guard does not decide who possesses disposition authority or what the disposition must be.
