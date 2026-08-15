# Upgrading IaaP Guard

## V1 patch upgrades

Review the release notes, update the pinned GitHub Action commit or deployed source
revision, and rerun `make validate` plus the relevant adoption preflight before relying
on new output.

For the GitHub App operator:

1. run the read-only `identity` and `verify` workflow operations;
2. create and inspect a non-executing CloudFormation change set with `plan`;
3. deploy only the exact reviewed main revision and change-set ARN;
4. verify the deployed operational contract; and
5. retain the run URL and rollback revision.

Repository adopters do not need AWS credentials or customer infrastructure credentials.

## Compatibility

V1 patch releases preserve the contracts frozen in
[`V1-CONTRACT-FREEZE.md`](V1-CONTRACT-FREEZE.md). Compare the version fields embedded
in machine-readable results rather than inferring compatibility from prose.

If a future release changes a schema, rule meaning, scoring model, planning contract,
membership trust, continuity semantic, conclusion authority, or App permission, it must
use a new contract version and publish migration guidance. Do not silently reinterpret
retained V1 evidence with a successor contract.

## Rollback

Re-pin the previous known-good Action commit or redeploy the previous reviewed App
revision. Machine-readable evidence retains immutable revisions and contract versions,
so rollback must not rewrite historical results.
