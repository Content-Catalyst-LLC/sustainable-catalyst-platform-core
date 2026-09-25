# Platform Core v3.30.0 — Prompt, Context & Retrieval Object Model

## Objective

v3.30.0 creates the governed semantic layer for prompt engineering, retrieval,
context assembly and evidence-aware RAG workflows.

It answers:

- Which prompt concept and exact prompt version were used?
- Which variables/messages composed that prompt?
- Which retrieval query was executed?
- Which corpora/sources/indexes were searched?
- Which embedding and reranker model versions were used?
- Which items were retrieved and at what ranks/scores?
- Which citations and source identities were preserved?
- Which retrieved items were admitted into the final model context?
- In what order and under what token budget was context assembled?
- Which inference run consumed that prompt/context bundle?

## Contract

`sc.core.prompt-context-retrieval.v1`

Depends on:
- `sc.core.ai-model.v1`
- `sc.core.ai-inference-provenance.v1`
- `sc.core.computational-job.v1`

## First-class objects

- PromptVariableDefinition
- PromptMessageTemplate
- PromptTemplate
- PromptVersion
- PromptVersionBinding
- RetrievalQuery
- RetrievedItem
- RetrievalResultSet
- ContextItem
- ContextAssembly
- RetrievalContextBundle

## Prompt versioning

PromptTemplate represents stable conceptual identity.

PromptVersion represents an immutable prompt configuration with ordered
messages, variable references, schema/content hashes, source commit and parent
version lineage.

This means inference provenance can refer to an exact prompt version rather
than an untracked string.

## Retrieval semantics

RetrievalQuery supports:
- keyword;
- semantic;
- hybrid;
- graph;
- citation;
- metadata;
- reranked;
- federated retrieval.

It can bind exact embedding and reranker AI model versions as well as a
ComputationalJob when retrieval itself is executed as governed compute.

RetrievedItem preserves:
- rank;
- source/document/chunk/evidence identity;
- retrieved content or content hash;
- retrieval score;
- rerank score;
- citation identity.

RetrievalResultSet binds those items to an exact retrieval query, retrieval
provider, retrieval index and index version.

## Context assembly

ContextAssembly records the precise evidence/context admitted into the model
window.

It preserves:
- item order;
- source/document/chunk/evidence refs;
- retrieved-item refs;
- content hashes;
- citations;
- inclusion reason;
- token counts;
- assembly policy;
- maximum context window;
- whether truncation was applied.

## Product boundaries

Knowledge Library owns:
- source ingestion;
- parsing/chunking;
- indexing;
- retrieval execution;
- document/chunk storage.

Research Librarian AI consumes those objects for research/RAG workflows.

Platform Core owns:
- stable identity;
- prompt/retrieval/context contracts;
- provenance;
- citation bindings;
- cross-product exchange semantics.

Core does not duplicate documents, chunks or vector indexes.

## RAG provenance chain

Source
→ Document
→ Chunk
→ RetrievalQuery
→ RetrievedItem
→ RetrievalResultSet
→ ContextAssembly
→ PromptVersion
→ AIInferenceRun
→ AIArtifact
→ Claim / Finding / Evidence

This is the bridge between Sustainable Catalyst's Knowledge Library and its AI
Engineering object system.

## Next

Platform Core v3.31.0 — AI Evaluation & Benchmark Object System.
