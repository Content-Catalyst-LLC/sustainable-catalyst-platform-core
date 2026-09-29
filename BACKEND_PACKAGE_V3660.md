# Platform Core v3.66.0 Backend Package

The v3.66.0 backend adds the `sc.core.linguistic-annotation-provenance.v1` contract and routes:

- `GET /public/v1/linguistic-annotations/contract`
- `GET /api/v1/linguistic-annotations/contract`
- `GET /api/v1/linguistic-annotations/reference`
- validation endpoints for annotation provenance, tokenizations, tokens, morphemes, morphology, POS, dependency parses/relations, constituency parses/nodes, and complete annotation bundles.

The contract extends `sc.core.multilingual-text-language-object.v1`. No database migration is required. Platform Core defines and validates annotation/provenance objects; external Workspace/Lab/Workbench/NLP runtimes perform tokenization, morphology, tagging, and parsing.
