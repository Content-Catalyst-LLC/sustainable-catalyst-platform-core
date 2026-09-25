from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256

CORE_RELEASE = "3.30.0"
CONTRACT_VERSION = "sc.core.prompt-context-retrieval.v1"
AI_MODEL_CONTRACT_VERSION = "sc.core.ai-model.v1"
AI_INFERENCE_CONTRACT_VERSION = "sc.core.ai-inference-provenance.v1"
COMPUTATIONAL_JOB_CONTRACT_VERSION = "sc.core.computational-job.v1"


class PromptRole(str, Enum):
    system = "system"
    developer = "developer"
    user = "user"
    assistant = "assistant"
    tool = "tool"
    other = "other"


class RetrievalStrategy(str, Enum):
    keyword = "keyword"
    semantic = "semantic"
    hybrid = "hybrid"
    graph = "graph"
    citation = "citation"
    metadata = "metadata"
    reranked = "reranked"
    federated = "federated"
    other = "other"


class ContextItemKind(str, Enum):
    source = "source"
    document = "document"
    chunk = "chunk"
    evidence = "evidence"
    claim = "claim"
    finding = "finding"
    dataset = "dataset"
    ai_artifact = "ai-artifact"
    conversation = "conversation"
    tool_result = "tool-result"
    metadata = "metadata"
    other = "other"


class PromptVariableDefinition(BaseModel):
    variable_id: str = Field(min_length=2, max_length=240)
    name: str = Field(min_length=1, max_length=200)
    data_type: Literal[
        "string", "number", "integer", "boolean", "object", "array", "reference", "other"
    ] = "string"
    required: bool = True
    description: str | None = Field(default=None, max_length=4000)
    default_value: Any = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class PromptMessageTemplate(BaseModel):
    message_id: str = Field(min_length=2, max_length=240)
    ordinal: int = Field(ge=1)
    role: PromptRole
    template: str = Field(min_length=1, max_length=200000)
    variable_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PromptTemplate(BaseModel):
    prompt_id: str = Field(min_length=2, max_length=240)
    name: str = Field(min_length=1, max_length=300)
    purpose: str | None = Field(default=None, max_length=10000)
    variables: list[PromptVariableDefinition] = Field(default_factory=list)
    model_family_constraints: list[str] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_variables(self):
        ids = [item.variable_id for item in self.variables]
        if len(ids) != len(set(ids)):
            raise ValueError("prompt variable ids must be unique")
        names = [item.name for item in self.variables]
        if len(names) != len(set(names)):
            raise ValueError("prompt variable names must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class PromptVersion(BaseModel):
    prompt_version_id: str = Field(min_length=2, max_length=300)
    prompt_id: str = Field(min_length=2, max_length=240)
    version: str = Field(min_length=1, max_length=240)
    messages: list[PromptMessageTemplate] = Field(default_factory=list)
    variable_schema_sha256: str | None = Field(
        default=None, pattern=r"^[0-9a-f]{64}$"
    )
    rendered_content_sha256: str | None = Field(
        default=None, pattern=r"^[0-9a-f]{64}$"
    )
    source_commit: str | None = Field(default=None, max_length=240)
    parent_prompt_version_ref: str | None = Field(default=None, max_length=300)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_messages(self):
        if self.parent_prompt_version_ref == self.prompt_version_id:
            raise ValueError("parent_prompt_version_ref cannot reference itself")
        message_ids = [item.message_id for item in self.messages]
        if len(message_ids) != len(set(message_ids)):
            raise ValueError("prompt message ids must be unique")
        ordinals = [item.ordinal for item in self.messages]
        if ordinals and sorted(ordinals) != list(range(1, len(ordinals) + 1)):
            raise ValueError("prompt message ordinals must be contiguous starting at 1")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("created_at", None)
        return canonical_sha256(payload)


class PromptVersionBinding(BaseModel):
    prompt: PromptTemplate
    prompt_version: PromptVersion

    @model_validator(mode="after")
    def validate_binding(self):
        if self.prompt.prompt_id != self.prompt_version.prompt_id:
            raise ValueError("PromptVersion.prompt_id must match PromptTemplate.prompt_id")

        known_variables = {item.variable_id for item in self.prompt.variables}
        for message in self.prompt_version.messages:
            unknown = [ref for ref in message.variable_refs if ref not in known_variables]
            if unknown:
                raise ValueError(
                    "message variable_refs are not declared on prompt template: "
                    + ", ".join(unknown)
                )
        return self

    def fingerprint(self) -> str:
        return canonical_sha256({
            "prompt_fingerprint_sha256": self.prompt.fingerprint(),
            "prompt_version_fingerprint_sha256": self.prompt_version.fingerprint(),
        })


class RetrievalQuery(BaseModel):
    retrieval_query_id: str = Field(min_length=2, max_length=300)
    query_text: str | None = Field(default=None, max_length=100000)
    query_embedding_ref: str | None = Field(default=None, max_length=300)
    strategy: RetrievalStrategy
    corpus_refs: list[str] = Field(default_factory=list)
    source_scope_refs: list[str] = Field(default_factory=list)
    filters: dict[str, Any] = Field(default_factory=dict)
    top_k: int = Field(default=10, ge=1, le=10000)
    score_threshold: float | None = None
    embedding_model_version_ref: str | None = Field(default=None, max_length=300)
    reranker_model_version_ref: str | None = Field(default=None, max_length=300)
    computational_job_ref: str | None = Field(default=None, max_length=300)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_query(self):
        if self.query_text is None and self.query_embedding_ref is None:
            raise ValueError("retrieval query requires query_text or query_embedding_ref")
        if not self.corpus_refs and not self.source_scope_refs:
            raise ValueError("retrieval query requires corpus_refs or source_scope_refs")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("created_at", None)
        return canonical_sha256(payload)


class RetrievedItem(BaseModel):
    retrieved_item_id: str = Field(min_length=2, max_length=300)
    retrieval_query_ref: str = Field(min_length=2, max_length=300)
    rank: int = Field(ge=1)
    context_kind: ContextItemKind
    source_ref: str | None = Field(default=None, max_length=1000)
    document_ref: str | None = Field(default=None, max_length=300)
    chunk_ref: str | None = Field(default=None, max_length=300)
    evidence_ref: str | None = Field(default=None, max_length=300)
    content: Any = None
    content_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    retrieval_score: float | None = None
    rerank_score: float | None = None
    citation_ref: str | None = Field(default=None, max_length=300)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_item(self):
        if (
            self.source_ref is None
            and self.document_ref is None
            and self.chunk_ref is None
            and self.evidence_ref is None
            and self.content is None
        ):
            raise ValueError("retrieved item requires a source/document/chunk/evidence ref or content")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RetrievalResultSet(BaseModel):
    retrieval_result_set_id: str = Field(min_length=2, max_length=300)
    retrieval_query_ref: str = Field(min_length=2, max_length=300)
    items: list[RetrievedItem] = Field(default_factory=list)
    retrieval_provider_ref: str | None = Field(default=None, max_length=300)
    retrieval_index_ref: str | None = Field(default=None, max_length=300)
    index_version_ref: str | None = Field(default=None, max_length=300)
    latency_ms: float | None = Field(default=None, ge=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_result_set(self):
        ids = [item.retrieved_item_id for item in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("retrieved item ids must be unique")

        ranks = [item.rank for item in self.items]
        if len(ranks) != len(set(ranks)):
            raise ValueError("retrieved item ranks must be unique")

        for item in self.items:
            if item.retrieval_query_ref != self.retrieval_query_ref:
                raise ValueError("retrieved item query ref must match result set")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("created_at", None)
        payload.pop("latency_ms", None)
        return canonical_sha256(payload)


class ContextItem(BaseModel):
    context_item_id: str = Field(min_length=2, max_length=300)
    ordinal: int = Field(ge=1)
    context_kind: ContextItemKind
    source_ref: str | None = Field(default=None, max_length=1000)
    document_ref: str | None = Field(default=None, max_length=300)
    chunk_ref: str | None = Field(default=None, max_length=300)
    evidence_ref: str | None = Field(default=None, max_length=300)
    retrieved_item_ref: str | None = Field(default=None, max_length=300)
    content: Any = None
    content_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    citation_ref: str | None = Field(default=None, max_length=300)
    inclusion_reason: str | None = Field(default=None, max_length=4000)
    token_count: int | None = Field(default=None, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_context_item(self):
        if (
            self.source_ref is None
            and self.document_ref is None
            and self.chunk_ref is None
            and self.evidence_ref is None
            and self.retrieved_item_ref is None
            and self.content is None
        ):
            raise ValueError("context item requires a reference or content")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ContextAssembly(BaseModel):
    context_assembly_id: str = Field(min_length=2, max_length=300)
    prompt_version_ref: str | None = Field(default=None, max_length=300)
    retrieval_query_refs: list[str] = Field(default_factory=list)
    retrieval_result_set_refs: list[str] = Field(default_factory=list)
    items: list[ContextItem] = Field(default_factory=list)
    assembly_policy: Literal[
        "rank-order",
        "source-balanced",
        "evidence-priority",
        "chronological",
        "manual",
        "hybrid",
        "other",
    ] = "rank-order"
    max_context_tokens: int | None = Field(default=None, ge=1)
    total_context_tokens: int | None = Field(default=None, ge=0)
    truncation_applied: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_context(self):
        ids = [item.context_item_id for item in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("context item ids must be unique")
        ordinals = [item.ordinal for item in self.items]
        if ordinals and sorted(ordinals) != list(range(1, len(ordinals) + 1)):
            raise ValueError("context item ordinals must be contiguous starting at 1")
        if (
            self.total_context_tokens is not None
            and self.max_context_tokens is not None
            and self.total_context_tokens > self.max_context_tokens
            and not self.truncation_applied
        ):
            raise ValueError(
                "context exceeds max_context_tokens without truncation_applied"
            )
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("created_at", None)
        return canonical_sha256(payload)


class RetrievalContextBundle(BaseModel):
    prompt_binding: PromptVersionBinding
    retrieval_queries: list[RetrievalQuery] = Field(default_factory=list)
    retrieval_result_sets: list[RetrievalResultSet] = Field(default_factory=list)
    context_assembly: ContextAssembly
    inference_run_ref: str | None = Field(default=None, max_length=300)
    ai_model_version_ref: str | None = Field(default=None, max_length=300)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_bundle(self):
        query_ids = {item.retrieval_query_id for item in self.retrieval_queries}
        result_ids = {item.retrieval_result_set_id for item in self.retrieval_result_sets}

        missing_q = [
            ref for ref in self.context_assembly.retrieval_query_refs
            if ref not in query_ids
        ]
        if missing_q:
            raise ValueError(
                "context assembly references retrieval queries not present in bundle: "
                + ", ".join(missing_q)
            )

        missing_r = [
            ref for ref in self.context_assembly.retrieval_result_set_refs
            if ref not in result_ids
        ]
        if missing_r:
            raise ValueError(
                "context assembly references result sets not present in bundle: "
                + ", ".join(missing_r)
            )

        if (
            self.context_assembly.prompt_version_ref
            and self.context_assembly.prompt_version_ref
            != self.prompt_binding.prompt_version.prompt_version_id
        ):
            raise ValueError(
                "context assembly prompt_version_ref must match prompt binding"
            )

        result_query_refs = {
            item.retrieval_query_ref for item in self.retrieval_result_sets
        }
        if not result_query_refs.issubset(query_ids):
            raise ValueError(
                "retrieval result sets must reference queries present in bundle"
            )

        return self

    def fingerprint(self) -> str:
        return canonical_sha256({
            "prompt_binding_fingerprint_sha256": self.prompt_binding.fingerprint(),
            "retrieval_query_fingerprints": sorted(
                item.fingerprint() for item in self.retrieval_queries
            ),
            "retrieval_result_set_fingerprints": sorted(
                item.fingerprint() for item in self.retrieval_result_sets
            ),
            "context_assembly_fingerprint_sha256": self.context_assembly.fingerprint(),
            "inference_run_ref": self.inference_run_ref,
            "ai_model_version_ref": self.ai_model_version_ref,
            "metadata": self.metadata,
        })


def reference_prompt_context_retrieval() -> RetrievalContextBundle:
    prompt = PromptTemplate(
        prompt_id="prompt:research-evidence-synthesis",
        name="Research Evidence Synthesis",
        purpose="Synthesize retrieved evidence while preserving citations and uncertainty.",
        variables=[
            PromptVariableDefinition(
                variable_id="prompt-var:question",
                name="question",
                data_type="string",
                required=True,
            ),
            PromptVariableDefinition(
                variable_id="prompt-var:context",
                name="context",
                data_type="array",
                required=True,
            ),
        ],
        provenance={
            "purpose": "Platform Core v3.30.0 prompt/context/retrieval proof",
        },
    )
    prompt_version = PromptVersion(
        prompt_version_id="prompt-version:research-evidence-synthesis:1.0.0",
        prompt_id=prompt.prompt_id,
        version="1.0.0",
        messages=[
            PromptMessageTemplate(
                message_id="prompt-message:system",
                ordinal=1,
                role=PromptRole.system,
                template=(
                    "Use only the supplied research context. Preserve source "
                    "citations and distinguish evidence from inference."
                ),
            ),
            PromptMessageTemplate(
                message_id="prompt-message:user",
                ordinal=2,
                role=PromptRole.user,
                template="Question: {{question}}\nContext: {{context}}",
                variable_refs=[
                    "prompt-var:question",
                    "prompt-var:context",
                ],
            ),
        ],
        variable_schema_sha256="a" * 64,
        rendered_content_sha256="b" * 64,
        source_commit="reference-prompt-commit",
    )
    prompt_binding = PromptVersionBinding(
        prompt=prompt,
        prompt_version=prompt_version,
    )

    query = RetrievalQuery(
        retrieval_query_id="retrieval-query:reference-evidence-001",
        query_text="What evidence supports the reference research finding?",
        strategy=RetrievalStrategy.hybrid,
        corpus_refs=["knowledge-library:reference-corpus"],
        top_k=3,
        embedding_model_version_ref="ai-model-version:reference-embedding:1.0.0",
        reranker_model_version_ref="ai-model-version:reference-reranker:1.0.0",
        computational_job_ref="job:reference-retrieval-001",
        provenance={
            "retrieval_owner": "knowledge-library",
            "core_executes_retrieval": False,
        },
    )

    items = [
        RetrievedItem(
            retrieved_item_id="retrieved-item:reference-001",
            retrieval_query_ref=query.retrieval_query_id,
            rank=1,
            context_kind=ContextItemKind.chunk,
            source_ref="source:reference-paper",
            document_ref="document:reference-paper",
            chunk_ref="chunk:reference-paper:001",
            content="Reference evidence passage one.",
            content_sha256="c" * 64,
            retrieval_score=0.94,
            rerank_score=0.97,
            citation_ref="citation:reference-paper:001",
        ),
        RetrievedItem(
            retrieved_item_id="retrieved-item:reference-002",
            retrieval_query_ref=query.retrieval_query_id,
            rank=2,
            context_kind=ContextItemKind.evidence,
            source_ref="source:reference-dataset",
            evidence_ref="evidence:reference-observation",
            content="Reference evidence passage two.",
            content_sha256="d" * 64,
            retrieval_score=0.88,
            rerank_score=0.91,
            citation_ref="citation:reference-dataset:001",
        ),
    ]

    result_set = RetrievalResultSet(
        retrieval_result_set_id="retrieval-result-set:reference-evidence-001",
        retrieval_query_ref=query.retrieval_query_id,
        items=items,
        retrieval_provider_ref="knowledge-library:retrieval",
        retrieval_index_ref="knowledge-library:index:reference",
        index_version_ref="knowledge-library:index-version:reference:v1",
        latency_ms=18.4,
    )

    context = ContextAssembly(
        context_assembly_id="context-assembly:reference-evidence-001",
        prompt_version_ref=prompt_version.prompt_version_id,
        retrieval_query_refs=[query.retrieval_query_id],
        retrieval_result_set_refs=[result_set.retrieval_result_set_id],
        items=[
            ContextItem(
                context_item_id="context-item:reference-001",
                ordinal=1,
                context_kind=ContextItemKind.chunk,
                source_ref="source:reference-paper",
                document_ref="document:reference-paper",
                chunk_ref="chunk:reference-paper:001",
                retrieved_item_ref=items[0].retrieved_item_id,
                content=items[0].content,
                content_sha256=items[0].content_sha256,
                citation_ref=items[0].citation_ref,
                inclusion_reason="highest reranked evidence item",
                token_count=8,
            ),
            ContextItem(
                context_item_id="context-item:reference-002",
                ordinal=2,
                context_kind=ContextItemKind.evidence,
                source_ref="source:reference-dataset",
                evidence_ref="evidence:reference-observation",
                retrieved_item_ref=items[1].retrieved_item_id,
                content=items[1].content,
                content_sha256=items[1].content_sha256,
                citation_ref=items[1].citation_ref,
                inclusion_reason="independent corroborating evidence",
                token_count=8,
            ),
        ],
        assembly_policy="evidence-priority",
        max_context_tokens=4096,
        total_context_tokens=16,
        truncation_applied=False,
        provenance={
            "citation_preservation": True,
            "context_owner": "platform-core-contract",
        },
    )

    return RetrievalContextBundle(
        prompt_binding=prompt_binding,
        retrieval_queries=[query],
        retrieval_result_sets=[result_set],
        context_assembly=context,
        inference_run_ref="inference-run:reference-rag-001",
        ai_model_version_ref="ai-model-version:reference-research-model:1.0.0",
        metadata={
            "research_librarian_compatible": True,
            "knowledge_library_retrieval_compatible": True,
        },
    )


def contract_document() -> dict[str, Any]:
    reference = reference_prompt_context_retrieval()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "depends_on": [
            AI_MODEL_CONTRACT_VERSION,
            AI_INFERENCE_CONTRACT_VERSION,
            COMPUTATIONAL_JOB_CONTRACT_VERSION,
        ],
        "object_types": [
            "PromptVariableDefinition",
            "PromptMessageTemplate",
            "PromptTemplate",
            "PromptVersion",
            "PromptVersionBinding",
            "RetrievalQuery",
            "RetrievedItem",
            "RetrievalResultSet",
            "ContextItem",
            "ContextAssembly",
            "RetrievalContextBundle",
        ],
        "capabilities": {
            "stable_prompt_identity": True,
            "immutable_prompt_versions": True,
            "prompt_variable_schema": True,
            "ordered_prompt_messages": True,
            "retrieval_query_identity": True,
            "hybrid_retrieval_contract": True,
            "embedding_model_version_binding": True,
            "reranker_model_version_binding": True,
            "retrieval_result_provenance": True,
            "retrieval_score_capture": True,
            "rerank_score_capture": True,
            "citation_preservation": True,
            "ordered_context_assembly": True,
            "context_token_budget_capture": True,
            "context_item_content_hashing": True,
            "inference_run_binding": True,
        },
        "integration": {
            "knowledge_library_owns_retrieval_execution": True,
            "research_librarian_consumes_retrieval_objects": True,
            "core_owns_prompt_context_retrieval_semantics": True,
            "core_duplicates_document_or_chunk_storage": False,
            "core_duplicates_vector_index": False,
        },
        "reference": {
            "prompt_version_id": (
                reference.prompt_binding.prompt_version.prompt_version_id
            ),
            "context_assembly_id": reference.context_assembly.context_assembly_id,
            "bundle_fingerprint_sha256": reference.fingerprint(),
        },
        "boundaries": {
            "core_executes_retrieval": False,
            "core_materializes_documents": False,
            "core_builds_vector_indexes": False,
            "core_calls_model_for_inference": False,
            "core_selects_sources_autonomously": False,
            "core_owns_identity_lineage_and_exchange_contracts": True,
        },
    }
