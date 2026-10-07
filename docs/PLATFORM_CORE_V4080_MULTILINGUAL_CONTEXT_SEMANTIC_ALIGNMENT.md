# Platform Core v4.8.0 — Multilingual Context & Semantic Alignment

v4.8.0 connects the v3.65–v3.69 multilingual/linguistic foundation to the v4.1–v4.7 contextual-semantic stack.

## Purpose

Core can now represent multiple language-specific renderings of the same contextual material without replacing the original-language source or flattening linguistic and cultural differences into a single English semantic representation.

## Governed objects

- `ContextLanguageRepresentation` — authoritative original or derived translation/transliteration representation with immutable content hash and provenance.
- `ContextSemanticUnit` — source-span-bound contextual semantic unit carrying modality, epistemic/pragmatic annotations, and optional v4.7 context-graph references.
- `MultilingualContextAlignment` — directional source→target contextual relationship with review state, confidence, aligned dimensions, and divergence references.
- `SemanticDivergenceRecord` — first-class lexical, semantic, discourse, pragmatic, epistemic, referential, temporal, spatial, cultural, or historical divergence.
- `ContextGraphProjectionBinding` — candidate projection from multilingual context into a v4.7 context thread without mutating that graph.
- `MultilingualContextInterpretation` and `MultilingualContextSnapshot` — governed reviewed packaging and reproducible snapshot semantics.

## Architectural rules

1. Original language is analyzed first and remains authoritative.
2. Translation and transliteration are derived representations and never replace the original.
3. Semantic similarity is not semantic equivalence.
4. Translation correspondence is not concept identity.
5. Cultural and historical conditioning are preserved as explicit divergence rather than discarded as translation noise.
6. Cross-language context projections do not mutate the v4.7 graph or establish entity/object identity.
7. Reviewed alignments do not establish claim truth, evidence validity, or source authority.

## Reference fixture

The synthetic fixture uses a Chinese authoritative source with English and Spanish derived representations. The policy proposition is aligned across the three languages while preserving possibility modality. A second context unit uses `治理`, `governance`, and `gobernanza` to demonstrate culturally conditioned contextual correspondence rather than universal lexical equivalence. The Chinese proposition is projected into the v4.7 policy-topic thread only as a candidate contextual hypothesis.

## Migration

No database migration is introduced by v4.8.0.
