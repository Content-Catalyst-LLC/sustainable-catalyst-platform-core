# Platform Core v3.67.0 — Translation, Transliteration & Parallel-Text Alignment Objects

## Summary

v3.67.0 extends the original-language and linguistic-annotation foundation from v3.65–v3.66 with provenance-bearing translation, transliteration, and parallel-text alignment objects. Original-language text remains canonical; every translation or transliteration is an explicitly derived representation that preserves lineage to the source.

## Added

- Derived translation and transliteration representation objects.
- Translator, model, tool, pipeline, and review provenance.
- Target language and script identity for every derived representation.
- Explicit transliteration-scheme identity.
- Exact character-range parallel-text alignments preserving both source and target slices.
- Optional alignment references to v3.66 source tokens.
- Translation variant sets for competing or alternative renderings.
- Deterministic object and bundle fingerprints.
- Public contract endpoint: `/public/v1/translation-alignments/contract`.
- Private reference endpoint: `/api/v1/translation-alignments/reference`.

## Architectural rules

- Original-language source text remains canonical and immutable.
- Translation and transliteration are derived representations and never replace the source.
- Multiple translations may coexist for the same source text.
- Translation disagreement is preserved rather than silently adjudicated.
- Machine-generated translations, transliterations, and alignments remain advisory.
- Human review state is distinct from machine confidence.
- Core validates structure, source/target span integrity, provenance, and lineage but does not execute translation, transliteration, or alignment inference.

## Roadmap

- v3.68.0: Historical Language, Script, Orthography & Variant Identity.
- v3.69.0: Cross-Lingual Semantic & Linguistic Exchange Layer.
- v3.70.0–v3.76.0: preserved Graph Neural Network wave. The Core invariant remains: **GNN prediction ≠ graph fact**. Model-produced relationships are candidates/predictions until separately validated and promoted through evidence-aware workflows.

## Database

No database migration is required.
