# Platform Core v3.65.0 — Multilingual Text & Language Object Model

## Summary

v3.65.0 begins the Language & Linguistics series by making original-language text, language identity, script identity, textual structure, mixed-language spans, and source provenance first-class Platform Core research objects.

## Added

- BCP 47 language identities with optional ISO 639 metadata.
- ISO 15924 script identities and writing-direction metadata.
- Canonical UTF-8 source-text objects with immutable SHA-256 content identity.
- Source-provenance records that bind canonical text to the originating research/source object.
- Hierarchical text units with exact character-range bindings back to canonical source text.
- Mixed-language span bindings that preserve language and script identity inside a single textual object.
- Deterministic fingerprints for all v3.65 objects and bundles.
- Public contract endpoint: `/public/v1/language-text/contract`.
- Private reference endpoint: `/api/v1/language-text/reference`.

## Architectural rules

- Original-language source text is canonical.
- A translation never replaces the original-language source.
- Language and script are separate identities.
- Machine-assisted language identification remains advisory and provenance-bearing.
- Every text unit remains character-addressable back to its canonical source.

## Deliberately deferred

- Tokenization, morphology, POS and syntax annotations: v3.66.0.
- Translation, transliteration and parallel-text alignment objects: v3.67.0.
- Historical language/script/orthography/variant identity: v3.68.0.
- Cross-lingual semantic exchange: v3.69.0.

## Database

No database migration is required.
