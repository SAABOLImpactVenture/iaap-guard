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

Do not newly publish implementation or operational material from `iaap-guard-core` unless an explicit publication review determines it is necessary. This includes:

- evaluation-engine, rule, scoring, materiality, and Evidence Continuity implementation beyond approved public contracts;
- internal fixtures, mutation cases, regression tests, unreleased evaluation methods, and private heuristics;
- GitHub App token-exchange/runtime implementation and deployment templates;
- live physical resource names, IAM-role/policy internals, private repository revisions, workflow/job identifiers, secret-reference topology, or raw operational evidence when a sanitized result is sufficient;
- unreleased pricing, licensing, patent, trademark, or commercialization analysis; and
- customer data, private repository content, secrets, credentials, or nonpublic telemetry.

## Evidence publication rule

Public evidence should substantiate the narrow claim with the minimum implementation detail necessary. Prefer sanitized results, immutable public revisions, public contract versions, bounded acceptance outcomes, and evidence digests over raw infrastructure output or private implementation coordinates.

Historical public validation material is not made secret by this policy. Do not rewrite Git history solely to create the appearance that a prior disclosure did not occur. Future assurance evidence should follow this boundary.

## Legal status

This document is a publication-control policy. It does not identify an IP owner, change the existing Apache-2.0 license, revoke rights previously granted, determine patentability, or make a trademark or copyright-registration decision.
