# ADR 0002 — Classify architecture context before evaluating rules

## Status
Accepted for Phase 8.

## Context

The same technology token can be valid or invalid depending on architectural context.

Examples:

- `ProviderConfig` is legitimate behind a Crossplane product implementation but is a product-boundary violation when exposed as a developer-facing input.
- Terraform/TFE may be legitimate for bootstrap, brownfield, migration, unsupported resources, accredited workflows, or exceptions while still being inappropriate as the consumer product contract.
- negative fixtures and deny-lists intentionally contain dangerous terms.
- documentation may describe a prohibited path without granting the path authority.

A repository-wide keyword scanner would therefore generate misleading findings and erode trust in the product.

## Decision

IaaP Guard must classify analyzed artifacts before evaluating architecture rules.

V0 contexts are:

- `consumer-contract`
- `experience`
- `ai-authority`
- `control-plane-implementation`
- `bootstrap`
- `evidence`
- `documentation-fixture`
- `unknown`

Structured parsing is preferred to text matching. Text heuristics may supplement structured analysis after context is established.

Every finding must record the component context that made the rule applicable.

## Consequences

- `ProviderConfig` in implementation code is not automatically a failure.
- a forbidden tool named in an AI deny-list is not mistaken for granted authority.
- bootstrap repositories are not penalized for lacking consumer product APIs.
- rules become slightly more complex than grep but materially more credible.

## Guardrail

A future implementation must include explicit positive fixtures proving that legitimate implementation-layer terms and negative-test content do not trigger consumer-boundary failures.
