# Platform Core v3.66.0 — Linguistic Annotation, Token, Morphology & Syntax Provenance

## Purpose

v3.66.0 makes linguistic analysis a governed research-object layer over v3.65 canonical multilingual text. It preserves exact source offsets and the provenance of every human, imported, pipeline, or model-assisted annotation.

## Object model

`AnnotationProvenanceRecord` captures the source-content fingerprint, producer, method, tool/model versions, annotation scheme, review state, reviewer, and advisory status.

`TokenizationRecord` groups one tokenization layer for a v3.65 text unit. `TokenRecord` binds every token back to an exact canonical character slice and language/script identity.

`MorphemeRecord` binds a morpheme to an exact slice of its parent token. `MorphologicalAnnotation` stores lemmas, feature/value pairs, and morpheme membership. `PartOfSpeechAnnotation` supports Universal POS and language-specific/custom tagsets.

`DependencyParseRecord` and `DependencyRelation` preserve dependency structures; complete parses require one relation per token, exactly one root, and no cycles.

`ConstituencyParseRecord` and `ConstituencyNode` preserve tree-style phrase structure; complete parses require every declared node to be reachable from the root and reject cycles.

## Provenance rule

Machine-generated linguistic structure is evidence about an analysis, not a replacement for source text and not an authoritative truth claim. Confidence, model identity, tool identity, and review state remain separate fields.

## Execution boundary

Platform Core does not execute tokenizers, morphological analyzers, POS taggers, dependency parsers, or constituency parsers. Those computations belong to Workspace, Research Lab, Workbench, or other governed specialist runtimes. Core standardizes the objects they exchange.

## Forward compatibility

v3.67 can align translations and transliterations against the same canonical character/token references. v3.68 can attach historical-language and orthographic identities. v3.69 can exchange cross-lingual semantic structures without losing the source-level lineage established here.


## Preserved graph-neural roadmap

The v3.65–v3.69 language/linguistics series does not displace the planned v3.70–v3.76 Graph Neural Network wave. Linguistic objects created here are graph-ready research objects that can later participate in learned graph representations while preserving a strict distinction between model-predicted relationships and established evidence relationships.
