# Platform Core v3.65.0 — Multilingual Text & Language Object Model

## Purpose

v3.65.0 makes human-language source material a normal Platform Core research object while preserving the original-language-first architecture required for later linguistic, historical, translation, and cross-lingual research capabilities.

## Canonical model

`source object -> source provenance -> canonical UTF-8 text -> hierarchical text unit -> language/script span`

The canonical text is never silently replaced by an English or other translated representation. Translation is explicitly reserved as a derived representation for v3.67.0.

## Core objects

- `LanguageIdentity` — BCP 47 language identity plus optional ISO 639 identifiers, endonyms and alternate names.
- `ScriptIdentity` — ISO 15924 script identity, writing direction and Unicode-script metadata.
- `TextSourceProvenanceRecord` — binds a canonical text object to the source/research object and optional immutable source artifact.
- `CanonicalTextSource` — UTF-8 source content with SHA-256 identity and original-language invariants.
- `TextUnitRecord` — document/section/paragraph/sentence/passage/etc. units bound to exact character ranges of canonical source text.
- `LanguageSpanBinding` — language and script identity for ranges inside a text unit, including provenance-aware model-assisted assignments.
- `MultilingualTextLanguageBundle` — cross-validates object references and character-range integrity.

## Governance and provenance

Machine learning may propose language assignments, but Core does not convert a model proposal into authoritative linguistic truth. A model-assisted assignment must name its assigning object/runtime and remains advisory.

All textual units resolve to exact source-character ranges. This makes later OCR/HTR, transcription, normalization, annotation, transliteration, translation, entity extraction and interpretation layers capable of retaining an auditable lineage back to the canonical source.

## Product boundary

Platform Core defines the portable object model and invariants. Library ingests and preserves sources; Workspace and Workbench perform corpus/text computation; Research Lab runs reproducible computational-linguistics experiments; Research Librarian consumes the objects for discovery and reasoning.

Core v3.65.0 itself does not perform OCR/HTR, language detection, tokenization, parsing, translation or transliteration.

## Roadmap handoff

- v3.66.0 — Linguistic Annotation, Token, Morphology & Syntax Provenance
- v3.67.0 — Translation, Transliteration & Parallel-Text Alignment Objects
- v3.68.0 — Historical Language, Script, Orthography & Variant Identity
- v3.69.0 — Cross-Lingual Semantic & Linguistic Exchange Layer
