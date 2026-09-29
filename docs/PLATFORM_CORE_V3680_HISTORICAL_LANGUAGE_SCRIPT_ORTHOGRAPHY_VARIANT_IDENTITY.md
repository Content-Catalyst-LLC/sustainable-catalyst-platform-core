# Platform Core v3.68.0 — Historical Language, Script, Orthography & Variant Identity

## Contract
`sc.core.historical-language-script-orthography-variant.v1`

## Purpose
Adds governed identities for historical language stages, historical script variants, orthography profiles, exact source-bound historical variant attestations, and derived normalization lineage.

## Architectural invariants
- Attested source text remains unchanged and canonical.
- Normalization/modernization is derived and provenance-bearing.
- Historical periodization and script identity may retain uncertainty.
- Machine-assisted identity or normalization is advisory.
- Core validates objects and lineage; it does not infer historical periodization, normalize source text, or adjudicate variant authority.
- v3.69 cross-lingual semantic exchange follows this release.
- v3.70–v3.76 Graph Neural Network wave remains reserved; GNN prediction is not a graph fact.

## Database migration
None.
