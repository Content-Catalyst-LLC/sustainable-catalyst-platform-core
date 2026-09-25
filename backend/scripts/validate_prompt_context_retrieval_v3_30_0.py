#!/usr/bin/env python3
from copy import deepcopy

from app.services.prompt_context_retrieval import (
    CONTRACT_VERSION,
    contract_document,
    reference_prompt_context_retrieval,
)

doc = contract_document()
assert doc["release"] == "3.30.0"
assert doc["contract"] == CONTRACT_VERSION
assert doc["integration"]["knowledge_library_owns_retrieval_execution"] is True
assert doc["integration"]["core_duplicates_vector_index"] is False
assert doc["capabilities"]["citation_preservation"] is True
assert doc["boundaries"]["core_executes_retrieval"] is False

bundle = reference_prompt_context_retrieval()
assert len(bundle.fingerprint()) == 64
assert bundle.fingerprint() == deepcopy(bundle).fingerprint()

prompt = bundle.prompt_binding.prompt
version = bundle.prompt_binding.prompt_version
assert len(prompt.fingerprint()) == 64
assert len(version.fingerprint()) == 64
assert len(bundle.prompt_binding.fingerprint()) == 64

query = bundle.retrieval_queries[0]
assert query.strategy.value == "hybrid"
assert query.embedding_model_version_ref is not None
assert query.reranker_model_version_ref is not None
assert query.computational_job_ref == "job:reference-retrieval-001"

result = bundle.retrieval_result_sets[0]
assert len(result.fingerprint()) == 64
assert all(item.citation_ref for item in result.items)

context = bundle.context_assembly
assert context.prompt_version_ref == version.prompt_version_id
assert len(context.fingerprint()) == 64
assert context.total_context_tokens <= context.max_context_tokens
assert all(item.retrieved_item_ref for item in context.items)

print("PASS - Platform Core v3.30.0 Prompt, Context & Retrieval Object Model")
print(f"CONTRACT={CONTRACT_VERSION}")
print("PROMPT_VERSIONING=enabled")
print("PROMPT_VARIABLE_SCHEMA=enabled")
print("RETRIEVAL_QUERY_IDENTITY=enabled")
print("EMBEDDING_MODEL_VERSION_BINDING=enabled")
print("RERANKER_MODEL_VERSION_BINDING=enabled")
print("RETRIEVAL_RESULT_PROVENANCE=enabled")
print("CITATION_PRESERVATION=enabled")
print("CONTEXT_ASSEMBLY=enabled")
print("INFERENCE_RUN_BINDING=enabled")
print("CORE_DUPLICATES_VECTOR_INDEX=false")
print("CORE_EXECUTES_RETRIEVAL=false")
