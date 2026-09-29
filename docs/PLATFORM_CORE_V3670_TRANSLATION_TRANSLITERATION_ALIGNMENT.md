# Platform Core v3.67.0 — Translation, Transliteration & Parallel-Text Alignment Objects

## Contract

`sc.core.translation-transliteration-alignment.v1`

## Purpose

Define governed objects for derived translations, transliterations, and parallel-text alignments while preserving original-language text as the canonical source of record.

## Object model

- `DerivationProvenanceRecord` — translator/model/tool/pipeline lineage, source hash binding, review state, and advisory-machine-output semantics.
- `DerivedTextRepresentation` — non-canonical translation or transliteration with target language/script identity and immutable content hash.
- `ParallelTextAlignmentRecord` — exact source/target character spans with optional v3.66 source-token references.
- `RepresentationVariantSet` — alternative renderings of one source unit without Core selecting a preferred translation.
- `TranslationTransliterationAlignmentBundle` — validated package spanning v3.65 source text, v3.66 linguistic annotations, derived representations, alignments, and variants.

## Invariants

1. Original-language source text remains canonical and immutable.
2. Translation and transliteration never replace the original.
3. Transliteration preserves a source-language identity while changing representation/script.
4. Machine-produced translations, transliterations, and alignments remain advisory.
5. Multiple translations may coexist; disagreement is preserved rather than silently adjudicated.
6. Core validates lineage and span integrity but does not perform translation, transliteration, or alignment inference.
7. The v3.70–v3.76 GNN roadmap remains reserved and `GNN prediction ≠ graph fact` remains an explicit architecture invariant.

## API

- `GET /public/v1/translation-alignments/contract`
- `GET /api/v1/translation-alignments/contract`
- `GET /api/v1/translation-alignments/reference`
- Validation POST routes for provenance, representations, alignments, variant sets, and complete bundles.

## Database

No migration is required in v3.67.0.
