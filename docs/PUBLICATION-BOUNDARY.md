# Public Publication Boundary

This repository is IaaP Guard's public product, interface, adoption, and assurance surface. It should provide enough information to install, integrate with, evaluate, and trust the hosted product without reproducing the private evaluation engine, rule implementation, runtime, deployment implementation, internal tests, or other nonpublic know-how.

## Publish deliberately

Public Guard material may include:

- installation, adoption, support, security, and upgrade guidance;
- deliberately public schemas and interface contracts;
- high-level product, architecture, and authority boundaries;
- known limitations that adopters need to understand;
- sanitized validation and assurance evidence; and
- public compatibility information required for supported integrations.

## Keep private

Private implementation may be represented publicly only by a deliberately published interface, a sanitized assurance result, or other minimum-necessary material that passes publication review. Publication review does not move private source or operational evidence into the public surface by default. Material kept private includes:

- evaluation-engine, rule, scoring, materiality, and Evidence Continuity implementation beyond approved public contracts;
- internal fixtures, mutation cases, regression tests, unreleased evaluation methods, and private heuristics;
- GitHub App token-exchange/runtime implementation and deployment templates; and
- unreleased pricing, licensing, patent, trademark, or commercialization analysis.

## Never publish

These prohibitions are unconditional. A publication review cannot override them.

- Customer data and private repository content, including snippets, file contents, webhook payloads, archives, or derived content that could reconstruct the private source.
- Secrets, credentials, tokens, and private keys, including their values, recoverable encodings, or material that enables their use.
- Internal operational topology, including live physical resource names, private repository revisions, workflow or job identifiers, IAM-role or policy internals, secret-reference graphs, and raw operational evidence when a sanitized result or digest is sufficient.
- Nonpublic telemetry that identifies a customer, private repository, credential path, or internal deployment topology.

Secret-manager storage is not repository storage. Public guidance may state that a deployment keeps secrets in an operator-controlled secret manager rather than repository content, but it must not publish secret values, live secret identifiers, reference topology, rotation material, or access paths.

## Evidence publication rule

Public evidence should substantiate the narrow claim with the minimum implementation detail necessary. Prefer sanitized results, immutable public revisions, public contract versions, bounded acceptance outcomes, and evidence digests over raw infrastructure output or private implementation coordinates.

The current claim-to-evidence ledger is [Public Guard Assurance Evidence](ASSURANCE-EVIDENCE.md). It records both verified outcomes and what remains unestablished so a point-in-time observation is not promoted into a production-readiness claim.

Historical public validation material is not made secret by this policy. Do not rewrite Git history solely to create the appearance that a prior disclosure did not occur. Future assurance evidence should follow this boundary.

## Legal status

This document is a publication-control policy. It does not identify an IP owner, change the existing Apache-2.0 license, revoke rights previously granted, determine patentability, or make a trademark or copyright-registration decision.
