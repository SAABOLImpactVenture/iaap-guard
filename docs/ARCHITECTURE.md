# IaaP Guard V0 Architecture

## Architectural center

The center of IaaP Guard is the deterministic rule/evidence engine, not GitHub Actions, a GitHub App, a hosted service, or AI.

```text
Repository / PR files
        ↓
Component classifier
        ↓
Structured parsers
        ↓
Versioned rule catalog
        ↓
Rule evaluation
        ↓
Normalized result
        ↓
Score + findings
```

Adapters consume the same normalized core:

```text
                   ┌─ CLI
IaaP Guard Core ───┼─ GitHub Action
                   └─ GitHub App
```

## Why classification comes first

A global keyword scanner would create structurally wrong findings.

Examples:

- `ProviderConfig` may be valid inside a Crossplane implementation but invalid as a developer-facing product input.
- Terraform/TFE may be a legitimate bootstrap, migration, brownfield or exception mechanism but should not automatically define the consumer product contract.
- negative fixtures intentionally contain forbidden patterns and must not be reported as live violations.
- documentation may describe a prohibited authority path without granting that authority.

Therefore rules evaluate **artifact + context**, not token presence alone.

## Classifier contract

The V0 classifier assigns one or more component contexts:

- `consumer-contract`
- `experience`
- `ai-authority`
- `control-plane-implementation`
- `bootstrap`
- `evidence`
- `documentation-fixture`
- `unknown`

Classification must be explainable and included in scan evidence.

## Parser strategy

Prefer structured parsing before textual heuristics:

1. YAML/JSON object structure and known API kinds.
2. JSON Schema/OpenAPI/XRD/CRD property surfaces.
3. Backstage Template parameter and action structure.
4. explicit AI runtime/tool-policy structures.
5. Crossplane Composition/provider structures.
6. Terraform/OpenTofu HCL-aware analysis when introduced.
7. limited text-aware command detection only after context is known.

The scanner must not execute repository code.

## Deterministic core requirements

The core must:

- run without network access;
- require no customer credentials;
- produce the same normalized result for the same inputs and rule version;
- identify the exact ruleset and scoring model used;
- preserve file/location evidence where available;
- never grant itself infrastructure or repository mutation authority.

## GitHub-native progression

### Phase 8
Local deterministic core contract only.

### Phase 9
Use the same core in GitHub Actions for dogfood. The Action job itself can serve as the first repository check surface.

### Public installable beta
Wrap the same core with a stateless GitHub App webhook adapter. The adapter verifies webhooks, obtains an installation token, reads relevant repository/PR artifacts, runs the core, and writes a Check Run.

No persistent customer database is required for the first installable beta.

## Future AI boundary

AI may later explain findings, identify unfamiliar product terminology, or propose remediation. AI-generated interpretation must not alter deterministic V0 rule results unless a separately governed future ruleset explicitly introduces that behavior.
