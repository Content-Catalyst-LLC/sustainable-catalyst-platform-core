# Platform Core v2.39.0 Audit — Research Librarian Visual Explanation

## Scope

- Additive migration `0043`.
- Six new governed tables for explanations, nodes, relations, citations, views, and immutable snapshots.
- Citation coverage validation and Evidence Ledger/source-snapshot bindings.
- Renderer-neutral visual explanation compilation.
- Explicit Research Librarian and specialist-runtime handoff contracts.
- Public metadata/bundle surfaces and SDK helpers.
- WordPress status integration.

## Non-goals / preserved boundaries

Core does not retrieve sources, generate prose, choose citations, rank evidence, execute analysis models, perform layout/rendering, or automatically promote inferred claims to truth.

## Local release certification

- Release-critical regression set: 107 tests collected; all 107 passed across isolated capability groups.
- Migration `0043` description length: 258 characters, within the production `VARCHAR(300)` ledger contract.
- Both pristine v2.38→v2.39 upgrade and recoverable partial-`0043` states are covered.
- Dependency-free release validator, push-safe secret scan, Python compilation, PHP lint, JavaScript syntax, and shell syntax gates passed.
- Public SDK package versions and Developer Portal download routing are aligned to v2.39.0.
