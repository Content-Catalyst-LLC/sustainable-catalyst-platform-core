# Platform Core v3.66.0 — Linguistic Annotation, Token, Morphology & Syntax Provenance

## Summary

v3.66.0 extends the v3.65 original-language text model with provenance-bearing linguistic annotation objects. Tokens, morphemes, lemmas, morphological features, part-of-speech tags, dependency relations, and constituency structures become first-class Platform Core research objects without turning Core into an NLP execution runtime.

## Added

- Annotation provenance records with human, imported, pipeline, and model-assisted production methods.
- Explicit model/tool version references and human review state.
- Tokenization layers and token objects bound to exact v3.65 canonical text-unit character ranges.
- Morpheme objects bound to exact parent-token character ranges.
- Lemma and arbitrary morphology feature annotations.
- Universal POS plus language-specific/custom POS tags.
- Dependency parse and dependency relation objects with structural validation.
- Constituency parse and constituency node objects with cycle/reachability validation.
- Deterministic fingerprints for all v3.66 objects and complete bundles.
- Public contract endpoint: `/public/v1/linguistic-annotations/contract`.
- Private reference endpoint: `/api/v1/linguistic-annotations/reference`.

## Architectural rules

- Canonical v3.65 source text remains immutable.
- Linguistic annotations are derived representations; they never rewrite the source.
- Machine-produced annotations remain advisory and retain model/tool provenance.
- Human review state is preserved separately from machine confidence.
- Alternative annotation layers may coexist rather than being silently adjudicated by Core.
- Core validates object structure, lineage, span integrity, and parse integrity; specialist runtimes perform the actual NLP computation.

## Deliberately outside Core

Core does not tokenize text, perform morphological analysis, assign POS tags, parse dependency syntax, parse constituency syntax, resolve annotation disagreements, or promote model annotations to truth.

## Roadmap

- v3.67.0: Translation, Transliteration & Parallel-Text Alignment Objects.
- v3.68.0: Historical Language, Script, Orthography & Variant Identity.
- v3.69.0: Cross-Lingual Semantic & Linguistic Exchange Layer.
- v3.70.0–v3.76.0: preserved second neural wave for graph machine learning, graph embeddings, node/edge classification, candidate link prediction, anomaly detection, knowledge-graph representation learning, and evidence-graph neural validation. Predicted graph relationships remain model outputs/candidates, never factual evidence edges by default.

## Database

No database migration is required.
