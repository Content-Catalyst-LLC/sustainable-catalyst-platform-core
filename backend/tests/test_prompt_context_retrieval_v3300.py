from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.services.prompt_context_retrieval import (
    CONTRACT_VERSION,
    ContextAssembly,
    ContextItem,
    ContextItemKind,
    PromptMessageTemplate,
    PromptRole,
    PromptTemplate,
    PromptVariableDefinition,
    PromptVersion,
    PromptVersionBinding,
    RetrievalContextBundle,
    RetrievalQuery,
    RetrievalResultSet,
    RetrievalStrategy,
    RetrievedItem,
    contract_document,
    reference_prompt_context_retrieval,
)


def test_contract_declares_prompt_context_retrieval_system():
    doc = contract_document()
    assert doc["release"] == "3.30.0"
    assert doc["contract"] == CONTRACT_VERSION
    assert doc["integration"]["knowledge_library_owns_retrieval_execution"] is True
    assert doc["boundaries"]["core_executes_retrieval"] is False


def test_reference_bundle_is_valid():
    bundle = reference_prompt_context_retrieval()
    assert bundle.prompt_binding.prompt_version.version == "1.0.0"
    assert bundle.retrieval_queries
    assert bundle.retrieval_result_sets
    assert bundle.context_assembly.items


def test_prompt_fingerprint_is_stable():
    prompt = reference_prompt_context_retrieval().prompt_binding.prompt
    assert prompt.fingerprint() == deepcopy(prompt).fingerprint()
    assert len(prompt.fingerprint()) == 64


def test_prompt_rejects_duplicate_variable_ids():
    with pytest.raises(ValidationError):
        PromptTemplate(
            prompt_id="prompt:test",
            name="Test",
            variables=[
                PromptVariableDefinition(
                    variable_id="var:x",
                    name="x",
                ),
                PromptVariableDefinition(
                    variable_id="var:x",
                    name="y",
                ),
            ],
        )


def test_prompt_rejects_duplicate_variable_names():
    with pytest.raises(ValidationError):
        PromptTemplate(
            prompt_id="prompt:test",
            name="Test",
            variables=[
                PromptVariableDefinition(
                    variable_id="var:x",
                    name="same",
                ),
                PromptVariableDefinition(
                    variable_id="var:y",
                    name="same",
                ),
            ],
        )


def test_prompt_version_rejects_noncontiguous_message_ordinals():
    with pytest.raises(ValidationError):
        PromptVersion(
            prompt_version_id="prompt-version:test:1",
            prompt_id="prompt:test",
            version="1",
            messages=[
                PromptMessageTemplate(
                    message_id="message:test",
                    ordinal=2,
                    role=PromptRole.user,
                    template="Hello",
                ),
            ],
        )


def test_prompt_version_rejects_self_parent():
    with pytest.raises(ValidationError):
        PromptVersion(
            prompt_version_id="prompt-version:test:1",
            prompt_id="prompt:test",
            version="1",
            parent_prompt_version_ref="prompt-version:test:1",
        )


def test_prompt_version_fingerprint_ignores_created_at():
    version = reference_prompt_context_retrieval().prompt_binding.prompt_version
    assert version.fingerprint() == deepcopy(version).fingerprint()


def test_prompt_binding_rejects_wrong_prompt_id():
    bundle = reference_prompt_context_retrieval()
    version = deepcopy(bundle.prompt_binding.prompt_version)
    version.prompt_id = "prompt:other"
    with pytest.raises(ValidationError):
        PromptVersionBinding(
            prompt=bundle.prompt_binding.prompt,
            prompt_version=version,
        )


def test_prompt_binding_rejects_unknown_variable_reference():
    prompt = PromptTemplate(
        prompt_id="prompt:test",
        name="Test",
        variables=[],
    )
    version = PromptVersion(
        prompt_version_id="prompt-version:test:1",
        prompt_id="prompt:test",
        version="1",
        messages=[
            PromptMessageTemplate(
                message_id="message:test",
                ordinal=1,
                role=PromptRole.user,
                template="{{x}}",
                variable_refs=["var:x"],
            ),
        ],
    )
    with pytest.raises(ValidationError):
        PromptVersionBinding(prompt=prompt, prompt_version=version)


def test_retrieval_query_requires_text_or_embedding():
    with pytest.raises(ValidationError):
        RetrievalQuery(
            retrieval_query_id="retrieval-query:test",
            strategy=RetrievalStrategy.semantic,
            corpus_refs=["corpus:test"],
        )


def test_retrieval_query_requires_scope():
    with pytest.raises(ValidationError):
        RetrievalQuery(
            retrieval_query_id="retrieval-query:test",
            query_text="test",
            strategy=RetrievalStrategy.semantic,
        )


def test_retrieval_query_fingerprint_is_stable():
    query = reference_prompt_context_retrieval().retrieval_queries[0]
    assert query.fingerprint() == deepcopy(query).fingerprint()


def test_retrieved_item_requires_reference_or_content():
    with pytest.raises(ValidationError):
        RetrievedItem(
            retrieved_item_id="retrieved-item:test",
            retrieval_query_ref="retrieval-query:test",
            rank=1,
            context_kind=ContextItemKind.chunk,
        )


def test_retrieval_result_set_rejects_duplicate_ranks():
    query_ref = "retrieval-query:test"
    items = [
        RetrievedItem(
            retrieved_item_id="retrieved-item:1",
            retrieval_query_ref=query_ref,
            rank=1,
            context_kind=ContextItemKind.chunk,
            content="one",
        ),
        RetrievedItem(
            retrieved_item_id="retrieved-item:2",
            retrieval_query_ref=query_ref,
            rank=1,
            context_kind=ContextItemKind.chunk,
            content="two",
        ),
    ]
    with pytest.raises(ValidationError):
        RetrievalResultSet(
            retrieval_result_set_id="retrieval-result-set:test",
            retrieval_query_ref=query_ref,
            items=items,
        )


def test_retrieval_result_set_rejects_query_mismatch():
    with pytest.raises(ValidationError):
        RetrievalResultSet(
            retrieval_result_set_id="retrieval-result-set:test",
            retrieval_query_ref="retrieval-query:a",
            items=[
                RetrievedItem(
                    retrieved_item_id="retrieved-item:1",
                    retrieval_query_ref="retrieval-query:b",
                    rank=1,
                    context_kind=ContextItemKind.chunk,
                    content="one",
                )
            ],
        )


def test_retrieval_result_fingerprint_excludes_latency():
    result = reference_prompt_context_retrieval().retrieval_result_sets[0]
    other = deepcopy(result)
    other.latency_ms = 999.0
    assert result.fingerprint() == other.fingerprint()


def test_context_item_requires_reference_or_content():
    with pytest.raises(ValidationError):
        ContextItem(
            context_item_id="context-item:test",
            ordinal=1,
            context_kind=ContextItemKind.chunk,
        )


def test_context_assembly_rejects_noncontiguous_ordinals():
    with pytest.raises(ValidationError):
        ContextAssembly(
            context_assembly_id="context:test",
            items=[
                ContextItem(
                    context_item_id="context-item:test",
                    ordinal=2,
                    context_kind=ContextItemKind.chunk,
                    content="x",
                )
            ],
        )


def test_context_assembly_enforces_token_budget_semantics():
    with pytest.raises(ValidationError):
        ContextAssembly(
            context_assembly_id="context:test",
            max_context_tokens=10,
            total_context_tokens=11,
            truncation_applied=False,
        )


def test_context_assembly_fingerprint_is_stable():
    context = reference_prompt_context_retrieval().context_assembly
    assert context.fingerprint() == deepcopy(context).fingerprint()
    assert len(context.fingerprint()) == 64


def test_bundle_rejects_missing_query_reference():
    bundle = reference_prompt_context_retrieval()
    with pytest.raises(ValidationError):
        RetrievalContextBundle(
            prompt_binding=bundle.prompt_binding,
            retrieval_queries=[],
            retrieval_result_sets=bundle.retrieval_result_sets,
            context_assembly=bundle.context_assembly,
        )


def test_bundle_rejects_missing_result_set_reference():
    bundle = reference_prompt_context_retrieval()
    with pytest.raises(ValidationError):
        RetrievalContextBundle(
            prompt_binding=bundle.prompt_binding,
            retrieval_queries=bundle.retrieval_queries,
            retrieval_result_sets=[],
            context_assembly=bundle.context_assembly,
        )


def test_bundle_rejects_prompt_version_mismatch():
    bundle = reference_prompt_context_retrieval()
    context = deepcopy(bundle.context_assembly)
    context.prompt_version_ref = "prompt-version:other:1"
    with pytest.raises(ValidationError):
        RetrievalContextBundle(
            prompt_binding=bundle.prompt_binding,
            retrieval_queries=bundle.retrieval_queries,
            retrieval_result_sets=bundle.retrieval_result_sets,
            context_assembly=context,
        )


def test_bundle_fingerprint_is_stable():
    bundle = reference_prompt_context_retrieval()
    assert bundle.fingerprint() == deepcopy(bundle).fingerprint()
    assert len(bundle.fingerprint()) == 64


def test_reference_preserves_citations():
    bundle = reference_prompt_context_retrieval()
    assert all(item.citation_ref for item in bundle.context_assembly.items)


def test_reference_binds_embedding_and_reranker_versions():
    query = reference_prompt_context_retrieval().retrieval_queries[0]
    assert query.embedding_model_version_ref is not None
    assert query.reranker_model_version_ref is not None


def test_reference_context_items_trace_to_retrieved_items():
    bundle = reference_prompt_context_retrieval()
    retrieved_ids = {
        item.retrieved_item_id
        for result in bundle.retrieval_result_sets
        for item in result.items
    }
    assert all(
        item.retrieved_item_ref in retrieved_ids
        for item in bundle.context_assembly.items
    )


def test_core_does_not_duplicate_vector_index_or_documents():
    doc = contract_document()
    assert doc["integration"]["core_duplicates_document_or_chunk_storage"] is False
    assert doc["integration"]["core_duplicates_vector_index"] is False
