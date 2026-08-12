# IaaP Guard Adoption Prerequisites and Barrier Removal

## Purpose

IaaP Guard is intentionally low-authority, but a useful result still depends on a few GitHub and repository conditions being true. This guide separates **hard prerequisites** from **common adoption obstacles** so a team can diagnose why the App did not run, why product scope did not appear, or why a multi-repository assessment became `INCOMPLETE`.

Start here before opening a support issue or changing Guard permissions.

## Choose the operating mode first

IaaP Guard supports two adoption paths.

### Single-repository mode

Use this when the product contract, experience, implementation, policy, and evidence you want Guard to evaluate can be understood from one repository.

You get:

- repository architecture evaluation;
- `PASS`, `WARNING`, `FAIL`, and `NOT_APPLICABLE` rule semantics;
- PR-base Evidence Continuity on IaaP-relevant pull requests;
- `SUPPORTED`, `REVIEW REQUIRED`, or `NOT ESTABLISHED` continuity context; and
- an advisory Improvement Plan when deterministic findings exist.

### Multi-repository product mode

Use this when one logical infrastructure product is split across repositories such as:

- product contract;
- storefront / Backstage experience;
- control plane;
- implementation;
- governance policy;
- evidence; or
- integration tests.

You get everything above for the triggering repository plus:

- trusted reciprocal product membership;
- `product-assessment/v1`;
- cross-repository relationship evaluation;
- product-level findings and evidence score;
- `INCOMPLETE` semantics when required evidence cannot be trusted or acquired; and
- `product-planning-report/v1`.

## What Guard does **not** require from a repository team

Using the GitHub App does **not** require the team to provide:

- AWS, Azure, or GCP credentials;
- Kubernetes credentials;
- Terraform or TFE credentials;
- a personal access token;
- repository content-write permission;
- workflow or administration permission;
- a persistent customer database; or
- permission for Guard to provision, remediate, approve, merge, or deploy anything.

Guard reads GitHub repository evidence and writes only its GitHub Check.

## Single-repository prerequisites

Before expecting a normal `IaaP Guard / Architecture` Check:

1. **The IaaP Guard GitHub App must be installed with access to the repository.**
2. **The App registration must retain the supported authority contract:** Metadata read, Contents read, Pull requests read, Checks write.
3. **The App webhook must be active and receiving Pull request events.** The runtime handles `opened`, `synchronize`, `reopened`, and `ready_for_review` actions.
4. **The repository must have an accessible default branch and the pull request must have GitHub-resolved base/head SHAs.**
5. **The repository snapshot must fit within the current beta bounds.**
6. **The changed paths should include a supported analysis suffix when you expect the full architecture + continuity path.**

Supported analysis suffixes are:

```text
.yaml  .yml  .json  .tf  .tofu  .hcl  .md  .py  .sh
```

If a pull request changes only unsupported suffixes, Guard should publish the explicit **no relevant changes** result rather than downloading and rescanning the full repository.

## Current repository and file bounds

The public beta deliberately protects the runtime from unbounded repository input.

| Bound | Current V1 / beta limit |
|---|---:|
| Compressed repository archive | 25 MB |
| Archive members | 20,000 |
| Extracted regular-file bytes | 100 MB |
| Individual analyzed file | 1 MB |
| Multi-repository product members | 12 |
| Cross-repository relationship bundle | 20 MB |

The scanner ignores common generated/vendor locations such as `.git`, `.venv`, `venv`, `node_modules`, `vendor`, `dist`, `build`, `__pycache__`, `artifacts`, and `.work`.

If a legitimate product exceeds these bounds, do not solve that by weakening Guard's safety controls. First remove generated material from the evidence path, split an overly broad logical product boundary, or open a product request for a larger governed operating tier.

## Evidence Continuity prerequisites

Evidence Continuity is automatic for IaaP-relevant GitHub pull requests.

Guard needs:

- an immutable PR-base SHA supplied by GitHub;
- an immutable PR-head SHA supplied by GitHub; and
- successful deterministic scans of the relevant base/head states.

The PR cannot nominate its own baseline. For a Check rerequest, Guard resolves the current pull request again before choosing the base/head pair.

Interpret continuity carefully:

- **SUPPORTED** means Guard detected no material rule/finding change in its own evidence model.
- **REVIEW REQUIRED** means Guard detected a material change and prior Guard evidence should not be silently treated as still applicable.
- **NOT ESTABLISHED** means Guard could not establish a suitable comparison baseline.

None of those statuses is a legal, compliance, deployment, exception, or risk-acceptance decision.

## Multi-repository prerequisites

Multi-repository federation is intentionally stricter because reading a second repository creates a trust boundary.

### 1. Put `.iaap/product.yaml` on the **default branch** of every participating repository

A PR-local manifest does not activate live federation by itself. Guard reads trusted product membership from the default branch.

Use `schemaVersion: iaap-product/v1`.

Example:

```yaml
schemaVersion: iaap-product/v1

product:
  id: application-platform
  name: Application Platform
  owner: platform-team

repositories:
  - name: acme/platform-contracts
    roles:
      - product-contract
      - control-plane
      - governance
      - evidence
    required: true
    primary: true

  - name: acme/backstage-storefront
    roles:
      - experience
    required: true
```

### 2. Every participating repository must reciprocally declare the same product boundary

Guard compares the normalized product identity and membership signature, including:

- product `id`;
- product `name`;
- product `owner` when present;
- repository names;
- repository roles;
- `required` flags; and
- `primary` flags.

Best practice is to publish the same manifest file to every member repository. This reduces accidental drift even though the runtime compares the normalized membership signature rather than raw bytes.

### 3. The triggering repository must register itself

If the trusted manifest does not include the repository whose PR triggered Guard, product evaluation cannot proceed correctly.

### 4. Keep the product at 12 repositories or fewer in V1

If a platform contains more than 12 repositories, first decide whether they actually represent one product boundary. Split portfolio, implementation, or evidence repositories into separate logical products when appropriate instead of treating an entire organization as one product.

### 5. Use one GitHub owner / organization for automatic federation

V1 automatically federates only repositories under the same owner as the triggering repository.

Cross-organization product relationships may still be meaningful architecturally, but V1 will not use product federation as an information bridge across owners.

### 6. Keep participating repositories at the same visibility

V1 requires the same GitHub visibility for automatically federated members.

For example, an `internal` triggering repository will not automatically federate a `public` or `private` related repository. Guard intentionally avoids probing or crossing that boundary.

### 7. Install IaaP Guard with access to every required member repository

The App creates a separate short-lived token for each related repository and narrows that token to `contents:read`.

If the App is not installed on a required member—or the installation does not include that repository—the product should become `INCOMPLETE` rather than silently omit the member.

### 8. Every required member needs a usable default branch

Guard reads the trusted manifest from the default branch and resolves that branch to an immutable commit SHA before scanning the member.

### 9. Keep cross-repository relationship evidence within the bounded product bundle

Member repositories are scanned independently from their full bounded snapshots. For V1 cross-repository relationship evaluation, Guard builds a temporary derivative containing only `consumer-contract` and `experience` artifacts.

That relationship bundle is limited to 20 MB. If it cannot be built safely and completely, Guard records `IAP-PR002` and the relationship evaluation becomes `INCOMPLETE`.

## Repository roles supported by `iaap-product/v1`

- `product-contract`
- `experience`
- `control-plane`
- `governance`
- `evidence`
- `integration`
- `implementation`
- `other`

Each repository must have at least one role. Repository names must use `owner/name` form. Duplicate repository entries are invalid. A product may define at most one `primary: true` repository.

## Common obstacles and how to remove them

| What you see | Likely cause | What to check / do |
|---|---|---|
| No `IaaP Guard / Architecture` Check at all | App installation, webhook delivery, event subscription, or permission problem | Confirm the App is installed on the repository, webhook is active, Pull request events are subscribed, and Checks write is still granted. |
| `No relevant changes` when you expected a scan | PR changed only unsupported suffixes | Confirm at least one changed architecture/evidence path ends in `.yaml`, `.yml`, `.json`, `.tf`, `.tofu`, `.hcl`, `.md`, `.py`, or `.sh`. |
| Evidence Continuity is `NOT ESTABLISHED` | A trustworthy base comparison could not be established | Confirm the PR has a valid GitHub base SHA and the base snapshot can be scanned within beta limits. |
| Evidence Continuity is `REVIEW REQUIRED` but the GitHub Check is not failing | Expected Phase 14 behavior | Review the rule-state and finding deltas. Continuity is advisory; repository PASS/WARNING/FAIL still owns the Check conclusion. |
| No **Product Assessment** section | No trusted default-branch product manifest on the triggering repository | Merge `.iaap/product.yaml` to the default branch first. A manifest only in the open PR is intentionally not trusted for enrollment. |
| Product is `INCOMPLETE` | Required member evidence is missing or relationship evaluation could not complete | Check App access, reciprocal manifest, owner, visibility, default branch, repository/archive bounds, and the 20 MB relationship bundle. |
| One member is missing even though it is listed | Guard cannot establish trusted reciprocal access | Confirm the App installation includes that repo, same owner/visibility is used, and the member default branch carries the matching manifest. |
| Product fails while every repository individually scores 100 | Cross-repository relationship drift | This is a valid product-level outcome. Inspect `IAP-C001` for storefront/consumer constraints that are broader or incompatible with the canonical product contract. |
| Product relationship shows `IAP-PR002` | Relationship evidence was missing, unsafe, or exceeded the bounded bundle | Reduce/split the relationship evidence, remove generated content, or narrow the declared product boundary. |
| Archive/snapshot too large | Repository exceeds public-beta safety limits | Remove generated/vendor material from the repository evidence path, split the repository/product, or request a larger governed tier. |
| More than 12 repositories are required | Product boundary is broader than V1 | Split into smaller logical products or wait for an explicitly governed higher-scale federation contract. |
| Related repo is public while trigger is internal/private | Visibility mismatch | Align visibility or keep the relationship outside automatic V1 federation. |
| Related repo belongs to another organization | Owner boundary | V1 does not automatically federate across owners. |
| Product score remains below expected after remediation | Another member or cross-repository finding still exists | Read the Product Assessment member table, weakest-member score, relationship findings, and evidence completeness rather than relying only on the aggregate number. |

## A useful multi-repository failure is not an App failure

The Phase 12 live acceptance proof demonstrated an important behavior: both real member repositories independently scored **100**, while trusted federation correctly failed the logical product at **96** because the Backstage storefront's `region` constraints were broader than the canonical product contract.

Guard emitted `IAP-C001` and generated a product Improvement Plan. After the storefront contract was corrected, the same two-repository product revalidated at **SUCCESS 100**.

That means a product-level failure can be proof that federation is working correctly rather than proof that installation failed.

Canonical live evidence is retained in:

- `SAABOLImpactVenture/ai-powered-infrastructure-as-a-product/artifacts/phase-12/live-federation-acceptance.json`
- `SAABOLImpactVenture/ai-powered-infrastructure-as-a-product/artifacts/phase-14/live-acceptance.json`

## Preflight checklist

Before the first real product-aware PR, verify:

- [ ] IaaP Guard is installed on the triggering repository.
- [ ] IaaP Guard is installed on every required related repository.
- [ ] App permissions remain Metadata read, Contents read, Pull requests read, Checks write.
- [ ] Webhook is active and Pull request events are subscribed.
- [ ] Every product member has `.iaap/product.yaml` on its default branch.
- [ ] Every member declares the same product identity and repository membership.
- [ ] Triggering repository is included in the manifest.
- [ ] Product has no more than 12 repositories.
- [ ] At most one repository is marked `primary: true`.
- [ ] All automatically federated repositories use the same GitHub owner.
- [ ] All automatically federated repositories use the same visibility.
- [ ] Every required repository has an accessible default branch.
- [ ] Repository archives fit within beta bounds.
- [ ] Relationship evidence can fit within the 20 MB product bundle.
- [ ] The test PR changes at least one supported file type when a full scan is expected.
- [ ] The team understands that product scope and Evidence Continuity are advisory and do not grant authorization.

## What to capture when asking for help

A useful support packet contains no secrets. Provide:

- repository name;
- PR number;
- `IaaP Guard / Architecture` Check Run URL or ID;
- observed repository result;
- observed Evidence Continuity status;
- observed Product Assessment conclusion, if present;
- `.iaap/product.yaml` from the trusted default branch, if using multi-repository scope;
- each member repository's owner, visibility, and default branch;
- whether the IaaP Guard App installation includes each required member; and
- the exact error or `IAP-*` finding text.

Do **not** provide GitHub App private keys, webhook secrets, installation tokens, cloud credentials, Kubernetes credentials, or PATs.

## Related documentation

- [`GITHUB-APP-BETA.md`](GITHUB-APP-BETA.md) — App registration, operator deployment, runtime authority, and beta bounds.
- [`MULTI-REPOSITORY-PRODUCTS.md`](MULTI-REPOSITORY-PRODUCTS.md) — product trust and federation semantics.
- [`PR-BASE-EVIDENCE-CONTINUITY.md`](PR-BASE-EVIDENCE-CONTINUITY.md) — PR-base/head continuity behavior.
- [`EVIDENCE-CONTINUITY.md`](EVIDENCE-CONTINUITY.md) — deterministic evidence model and authority boundary.
