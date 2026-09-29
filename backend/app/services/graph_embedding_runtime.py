from __future__ import annotations

import math
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .graph_machine_learning import (
    GraphMLFoundationBundle,
    GraphRunKind,
    reference_graph_ml_foundation_bundle,
)
from .machine_learning_models import ExecutionHost
from .ml_embedding_representation import MLSimilarityMetric, MLVectorDType

CORE_RELEASE = "3.71.0"
CONTRACT_VERSION = "sc.core.graph-embedding-runtime.v1"


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


def _finite(value: float, label: str) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{label} must be finite")


def _l2(values: list[float]) -> float:
    return math.sqrt(sum(v * v for v in values))


class GraphEmbeddingTargetKind(str, Enum):
    node = "node"
    edge = "edge"
    graph = "graph"


class GraphEmbeddingOperation(str, Enum):
    generate = "generate"
    index = "index"
    query = "query"
    project = "project"
    export = "export"


class GraphEmbeddingAggregation(str, Enum):
    none = "none"
    mean = "mean"
    sum = "sum"
    max = "max"
    attention = "attention"
    custom = "custom"


class GraphEmbeddingLifecycleState(str, Enum):
    generated = "generated"
    reviewed = "reviewed"
    deprecated = "deprecated"


class GraphEmbeddingRuntimeContract(BaseModel):
    embedding_runtime_contract_id: str = Field(min_length=2, max_length=500)
    extends_graph_ml_runtime_ref: str = Field(min_length=2, max_length=500)
    execution_host: ExecutionHost
    framework: str = Field(min_length=1, max_length=240)
    framework_version: str | None = Field(default=None, max_length=120)
    supported_operations: list[GraphEmbeddingOperation] = Field(min_length=1)
    supported_target_kinds: list[GraphEmbeddingTargetKind] = Field(min_length=1)
    required_capabilities: list[str] = Field(default_factory=list)
    core_executes_embedding_runtime: Literal[False] = False
    runtime_may_mutate_evidence_graph: Literal[False] = False
    similarity_query_may_create_evidence_edge: Literal[False] = False
    arbitrary_code_allowed_by_core: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_runtime(self):
        _unique([x.value for x in self.supported_operations], "embedding runtime operations")
        _unique([x.value for x in self.supported_target_kinds], "embedding runtime target kinds")
        _unique(self.required_capabilities, "embedding runtime required_capabilities")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class GraphEmbeddingSpaceContract(BaseModel):
    embedding_space_id: str = Field(min_length=2, max_length=500)
    snapshot_ref: str = Field(min_length=2, max_length=500)
    model_spec_ref: str = Field(min_length=2, max_length=500)
    graph_ml_task_ref: str = Field(min_length=2, max_length=500)
    embedding_runtime_contract_ref: str = Field(min_length=2, max_length=500)
    dimensions: int = Field(ge=1, le=1000000)
    dtype: MLVectorDType = MLVectorDType.float32
    similarity_metric: MLSimilarityMetric
    normalized: bool = False
    target_kinds: list[GraphEmbeddingTargetKind] = Field(min_length=1)
    aggregation: GraphEmbeddingAggregation = GraphEmbeddingAggregation.none
    feature_binding_refs: list[str] = Field(min_length=1)
    training_lineage_refs: list[str] = Field(min_length=1)
    created_by_embedding_run_ref: str = Field(min_length=2, max_length=500)
    index_artifact_ref: str | None = Field(default=None, max_length=1000)
    index_artifact_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    embedding_similarity_is_not_graph_fact: Literal[True] = True
    embedding_distance_is_not_evidence_strength: Literal[True] = True
    embedding_space_is_model_and_snapshot_specific: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_space(self):
        _unique([x.value for x in self.target_kinds], "embedding-space target_kinds")
        _unique(self.feature_binding_refs, "embedding-space feature_binding_refs")
        _unique(self.training_lineage_refs, "embedding-space training_lineage_refs")
        if self.index_artifact_sha256 and not self.index_artifact_ref:
            raise ValueError("index_artifact_sha256 requires index_artifact_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class GraphEmbeddingComputationProvenance(BaseModel):
    embedding_run_id: str = Field(min_length=2, max_length=500)
    graph_ml_run_ref: str = Field(min_length=2, max_length=500)
    snapshot_ref: str = Field(min_length=2, max_length=500)
    model_spec_ref: str = Field(min_length=2, max_length=500)
    embedding_runtime_contract_ref: str = Field(min_length=2, max_length=500)
    input_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    output_artifact_refs: list[str] = Field(min_length=1)
    environment_ref: str | None = Field(default=None, max_length=500)
    checkpoint_ref: str | None = Field(default=None, max_length=500)
    parameters: dict[str, Any] = Field(default_factory=dict)
    created_at: str | None = Field(default=None, max_length=80)
    output_is_derived_representation: Literal[True] = True
    output_is_not_evidence: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_run(self):
        _unique(self.output_artifact_refs, "embedding run output_artifact_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class GraphEmbeddingObject(BaseModel):
    embedding_id: str = Field(min_length=2, max_length=500)
    embedding_space_ref: str = Field(min_length=2, max_length=500)
    source_snapshot_ref: str = Field(min_length=2, max_length=500)
    target_kind: GraphEmbeddingTargetKind
    target_object_ref: str = Field(min_length=2, max_length=1000)
    dimensions: int = Field(ge=1, le=1000000)
    vector: list[float] | None = None
    vector_artifact_ref: str | None = Field(default=None, max_length=1000)
    vector_artifact_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    l2_norm: float | None = Field(default=None, ge=0.0)
    generated_by_embedding_run_ref: str = Field(min_length=2, max_length=500)
    source_feature_refs: list[str] = Field(default_factory=list)
    source_evidence_refs: list[str] = Field(default_factory=list)
    lifecycle_state: GraphEmbeddingLifecycleState = GraphEmbeddingLifecycleState.generated
    reviewer_ref: str | None = Field(default=None, max_length=1000)
    is_graph_fact: Literal[False] = False
    is_evidence_edge: Literal[False] = False
    embedding_does_not_establish_relationship: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_embedding(self):
        if self.vector is None and self.vector_artifact_ref is None:
            raise ValueError("graph embedding requires inline vector or vector_artifact_ref")
        if self.vector_artifact_sha256 and not self.vector_artifact_ref:
            raise ValueError("vector_artifact_sha256 requires vector_artifact_ref")
        if self.vector is not None:
            if len(self.vector) != self.dimensions:
                raise ValueError("graph embedding vector length must equal dimensions")
            for value in self.vector:
                _finite(value, "graph embedding vector value")
            actual = _l2(self.vector)
            if self.l2_norm is not None and not math.isclose(actual, self.l2_norm, rel_tol=1e-6, abs_tol=1e-6):
                raise ValueError("graph embedding l2_norm must match inline vector")
        if self.lifecycle_state != GraphEmbeddingLifecycleState.generated and not self.reviewer_ref:
            raise ValueError("reviewed/deprecated graph embedding requires reviewer_ref")
        _unique(self.source_feature_refs, "graph embedding source_feature_refs")
        _unique(self.source_evidence_refs, "graph embedding source_evidence_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class GraphSimilarityNeighbor(BaseModel):
    embedding_ref: str = Field(min_length=2, max_length=500)
    target_object_ref: str = Field(min_length=2, max_length=1000)
    rank: int = Field(ge=1)
    similarity_score: float
    raw_distance: float | None = Field(default=None, ge=0.0)

    @model_validator(mode="after")
    def validate_neighbor(self):
        _finite(self.similarity_score, "graph similarity score")
        if self.raw_distance is not None:
            _finite(self.raw_distance, "graph similarity raw_distance")
        return self


class GraphSimilarityQueryRecord(BaseModel):
    similarity_query_id: str = Field(min_length=2, max_length=500)
    embedding_space_ref: str = Field(min_length=2, max_length=500)
    query_embedding_ref: str = Field(min_length=2, max_length=500)
    metric: MLSimilarityMetric
    top_k: int = Field(ge=1, le=100000)
    neighbors: list[GraphSimilarityNeighbor] = Field(min_length=1)
    embedding_run_ref: str = Field(min_length=2, max_length=500)
    index_artifact_ref: str | None = Field(default=None, max_length=1000)
    created_at: str | None = Field(default=None, max_length=80)
    similarity_is_not_evidence: Literal[True] = True
    similarity_is_not_identity: Literal[True] = True
    similarity_is_not_relationship_validation: Literal[True] = True
    query_does_not_mutate_graph: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_query(self):
        if len(self.neighbors) > self.top_k:
            raise ValueError("similarity neighbor count cannot exceed top_k")
        refs = [x.embedding_ref for x in self.neighbors]
        ranks = [x.rank for x in self.neighbors]
        _unique(refs, "similarity neighbor embedding_refs")
        if self.query_embedding_ref in refs:
            raise ValueError("similarity query embedding cannot be its own neighbor")
        if sorted(ranks) != list(range(1, len(ranks) + 1)):
            raise ValueError("similarity neighbor ranks must be contiguous from 1")
        ordered = sorted(self.neighbors, key=lambda x: x.rank)
        if any(a.similarity_score < b.similarity_score for a, b in zip(ordered, ordered[1:])):
            raise ValueError("similarity scores must be non-increasing by rank")
        if self.metric == MLSimilarityMetric.cosine:
            if any(x.similarity_score < -1.0 or x.similarity_score > 1.0 for x in self.neighbors):
                raise ValueError("cosine similarity scores must be within [-1, 1]")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class GraphEmbeddingBundle(BaseModel):
    graph_ml_foundation_bundle: GraphMLFoundationBundle
    runtime_contracts: list[GraphEmbeddingRuntimeContract] = Field(min_length=1)
    embedding_runs: list[GraphEmbeddingComputationProvenance] = Field(min_length=1)
    embedding_spaces: list[GraphEmbeddingSpaceContract] = Field(min_length=1)
    embeddings: list[GraphEmbeddingObject] = Field(min_length=1)
    similarity_queries: list[GraphSimilarityQueryRecord] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_bundle(self):
        foundation = self.graph_ml_foundation_bundle
        snapshots = {x.snapshot_id: x for x in foundation.snapshots}
        tasks = {x.task_id: x for x in foundation.tasks}
        model_specs = {x.model_spec.model_spec_id: x.model_spec for x in foundation.model_foundations}
        graph_runtimes = {x.runtime_contract_id: x for x in foundation.runtime_contracts}
        graph_runs = {x.run_id: x for x in foundation.run_provenance}
        feature_bindings = {x.feature_binding_id: x for x in foundation.feature_bindings}

        runtime_by_id = {x.embedding_runtime_contract_id: x for x in self.runtime_contracts}
        run_by_id = {x.embedding_run_id: x for x in self.embedding_runs}
        space_by_id = {x.embedding_space_id: x for x in self.embedding_spaces}
        embedding_by_id = {x.embedding_id: x for x in self.embeddings}

        for label, values in (
            ("embedding runtime ids", list(runtime_by_id)),
            ("embedding run ids", list(run_by_id)),
            ("embedding space ids", list(space_by_id)),
            ("embedding ids", list(embedding_by_id)),
            ("similarity query ids", [x.similarity_query_id for x in self.similarity_queries]),
        ):
            _unique(values, label)

        for runtime in self.runtime_contracts:
            if runtime.extends_graph_ml_runtime_ref not in graph_runtimes:
                raise ValueError("embedding runtime must extend a v3.70 graph ML runtime")
            if runtime.execution_host != graph_runtimes[runtime.extends_graph_ml_runtime_ref].execution_host:
                raise ValueError("embedding runtime execution_host must match extended graph ML runtime")

        for run in self.embedding_runs:
            graph_run = graph_runs.get(run.graph_ml_run_ref)
            if graph_run is None:
                raise ValueError("embedding run graph_ml_run_ref must resolve")
            if graph_run.run_kind not in {GraphRunKind.embed, GraphRunKind.infer}:
                raise ValueError("embedding computation requires v3.70 embed or infer run lineage")
            if run.snapshot_ref != graph_run.snapshot_ref or run.model_spec_ref != graph_run.model_spec_ref:
                raise ValueError("embedding run lineage must match graph ML run snapshot/model")
            if run.embedding_runtime_contract_ref not in runtime_by_id:
                raise ValueError("embedding run runtime contract must resolve")

        for space in self.embedding_spaces:
            if space.snapshot_ref not in snapshots:
                raise ValueError("embedding space snapshot_ref must resolve")
            if space.model_spec_ref not in model_specs:
                raise ValueError("embedding space model_spec_ref must resolve")
            if space.graph_ml_task_ref not in tasks:
                raise ValueError("embedding space graph_ml_task_ref must resolve")
            if space.embedding_runtime_contract_ref not in runtime_by_id:
                raise ValueError("embedding space runtime contract must resolve")
            run = run_by_id.get(space.created_by_embedding_run_ref)
            if run is None:
                raise ValueError("embedding space created_by_embedding_run_ref must resolve")
            if run.snapshot_ref != space.snapshot_ref or run.model_spec_ref != space.model_spec_ref:
                raise ValueError("embedding space run lineage must match snapshot/model")
            if set(space.feature_binding_refs) - set(feature_bindings):
                raise ValueError("embedding space feature_binding_refs must resolve")

        seen_targets: set[str] = set()
        for embedding in self.embeddings:
            space = space_by_id.get(embedding.embedding_space_ref)
            if space is None:
                raise ValueError("embedding embedding_space_ref must resolve")
            if embedding.source_snapshot_ref != space.snapshot_ref:
                raise ValueError("embedding source snapshot must match embedding space")
            if embedding.generated_by_embedding_run_ref != space.created_by_embedding_run_ref:
                raise ValueError("embedding run must match embedding space creation run")
            if embedding.dimensions != space.dimensions:
                raise ValueError("embedding dimensions must match embedding space")
            if embedding.target_kind not in space.target_kinds:
                raise ValueError("embedding target kind not supported by embedding space")
            snapshot = snapshots[space.snapshot_ref]
            if embedding.target_kind == GraphEmbeddingTargetKind.node and embedding.target_object_ref not in snapshot.node_refs:
                raise ValueError("node embedding target must resolve to snapshot node")
            if embedding.target_kind == GraphEmbeddingTargetKind.edge:
                edge_refs = {x.evidence_edge_ref for x in snapshot.evidence_edges}
                if embedding.target_object_ref not in edge_refs:
                    raise ValueError("edge embedding target must resolve to snapshot evidence edge")
            if embedding.target_kind == GraphEmbeddingTargetKind.graph and embedding.target_object_ref != snapshot.source_graph_ref:
                raise ValueError("graph embedding target must resolve to source graph")
            key = f"{embedding.embedding_space_ref}|{embedding.target_kind.value}|{embedding.target_object_ref}"
            if key in seen_targets:
                raise ValueError("target may have at most one embedding per embedding space")
            seen_targets.add(key)
            if space.normalized and embedding.vector is not None:
                if not math.isclose(_l2(embedding.vector), 1.0, rel_tol=1e-6, abs_tol=1e-6):
                    raise ValueError("inline vector in normalized graph embedding space must have L2 norm 1")

        for query in self.similarity_queries:
            space = space_by_id.get(query.embedding_space_ref)
            if space is None:
                raise ValueError("similarity query embedding_space_ref must resolve")
            query_embedding = embedding_by_id.get(query.query_embedding_ref)
            if query_embedding is None or query_embedding.embedding_space_ref != space.embedding_space_id:
                raise ValueError("similarity query embedding must resolve in same space")
            if query.metric != space.similarity_metric:
                raise ValueError("similarity query metric must match embedding space")
            if query.embedding_run_ref != space.created_by_embedding_run_ref:
                raise ValueError("similarity query embedding_run_ref must match embedding space lineage")
            for neighbor in query.neighbors:
                candidate = embedding_by_id.get(neighbor.embedding_ref)
                if candidate is None or candidate.embedding_space_ref != space.embedding_space_id:
                    raise ValueError("similarity neighbor embedding must resolve in same space")
                if candidate.target_object_ref != neighbor.target_object_ref:
                    raise ValueError("similarity neighbor target_object_ref must match embedding")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


def reference_graph_embedding_bundle() -> GraphEmbeddingBundle:
    foundation = reference_graph_ml_foundation_bundle()
    snapshot = foundation.snapshots[0]
    task = foundation.tasks[0]
    model_spec = foundation.model_foundations[0].model_spec
    graph_runtime = foundation.runtime_contracts[0]
    graph_embed_run = next((x for x in foundation.run_provenance if x.run_kind == GraphRunKind.embed), None)
    if graph_embed_run is None:
        # v3.70 reference has train+infer. Reuse inference as the governed upstream computation lineage.
        graph_embed_run = next(x for x in foundation.run_provenance if x.run_kind == GraphRunKind.infer)

    runtime = GraphEmbeddingRuntimeContract(
        embedding_runtime_contract_id="graph-embedding-runtime:reference:v1",
        extends_graph_ml_runtime_ref=graph_runtime.runtime_contract_id,
        execution_host=ExecutionHost.workspace,
        framework="pytorch-geometric-compatible",
        framework_version="external",
        supported_operations=[GraphEmbeddingOperation.generate, GraphEmbeddingOperation.index, GraphEmbeddingOperation.query, GraphEmbeddingOperation.export],
        supported_target_kinds=[GraphEmbeddingTargetKind.node, GraphEmbeddingTargetKind.edge, GraphEmbeddingTargetKind.graph],
        required_capabilities=["graph-embedding-generation", "vector-indexing", "similarity-query"],
        metadata={"synthetic_reference": True, "workspace_computes": True},
    )
    embedding_run = GraphEmbeddingComputationProvenance(
        embedding_run_id="graph-embedding-run:reference:v1",
        graph_ml_run_ref=graph_embed_run.run_id,
        snapshot_ref=snapshot.snapshot_id,
        model_spec_ref=model_spec.model_spec_id,
        embedding_runtime_contract_ref=runtime.embedding_runtime_contract_id,
        input_fingerprint_sha256=snapshot.fingerprint(),
        output_artifact_refs=["artifact:reference:graph-embeddings:v1", "artifact:reference:graph-vector-index:v1"],
        environment_ref=model_spec.runtime_bindings[0].environment_ref,
        checkpoint_ref="artifact:reference:graph-model-checkpoint:v1",
        parameters={"dimensions": 8, "normalization": "l2"},
        created_at="2026-09-29T03:02:00-05:00",
        metadata={"synthetic_reference": True},
    )
    feature_ref = foundation.feature_bindings[0].feature_binding_id
    space = GraphEmbeddingSpaceContract(
        embedding_space_id="graph-embedding-space:reference:nodes:v1",
        snapshot_ref=snapshot.snapshot_id,
        model_spec_ref=model_spec.model_spec_id,
        graph_ml_task_ref=task.task_id,
        embedding_runtime_contract_ref=runtime.embedding_runtime_contract_id,
        dimensions=8,
        dtype=MLVectorDType.float32,
        similarity_metric=MLSimilarityMetric.cosine,
        normalized=True,
        target_kinds=[GraphEmbeddingTargetKind.node],
        aggregation=GraphEmbeddingAggregation.none,
        feature_binding_refs=[feature_ref],
        training_lineage_refs=[x.run_id for x in foundation.run_provenance if x.run_kind == GraphRunKind.train],
        created_by_embedding_run_ref=embedding_run.embedding_run_id,
        index_artifact_ref="artifact:reference:graph-vector-index:v1",
        index_artifact_sha256=canonical_sha256({"fixture": "graph-vector-index", "version": 1}),
        metadata={"synthetic_reference": True},
    )
    vectors = [
        [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.8, 0.6, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.6, 0.8, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    ]
    embeddings: list[GraphEmbeddingObject] = []
    for idx, (node_ref, vector) in enumerate(zip(snapshot.node_refs, vectors), start=1):
        embeddings.append(GraphEmbeddingObject(
            embedding_id=f"graph-embedding:reference:node:{idx}:v1",
            embedding_space_ref=space.embedding_space_id,
            source_snapshot_ref=snapshot.snapshot_id,
            target_kind=GraphEmbeddingTargetKind.node,
            target_object_ref=node_ref,
            dimensions=8,
            vector=vector,
            l2_norm=1.0,
            generated_by_embedding_run_ref=embedding_run.embedding_run_id,
            source_feature_refs=[feature_ref],
            source_evidence_refs=[x.evidence_edge_ref for x in snapshot.evidence_edges],
            metadata={"synthetic_reference": True},
        ))
    query = GraphSimilarityQueryRecord(
        similarity_query_id="graph-similarity-query:reference:node-1:v1",
        embedding_space_ref=space.embedding_space_id,
        query_embedding_ref=embeddings[0].embedding_id,
        metric=MLSimilarityMetric.cosine,
        top_k=2,
        neighbors=[
            GraphSimilarityNeighbor(embedding_ref=embeddings[1].embedding_id, target_object_ref=embeddings[1].target_object_ref, rank=1, similarity_score=0.8),
            GraphSimilarityNeighbor(embedding_ref=embeddings[2].embedding_id, target_object_ref=embeddings[2].target_object_ref, rank=2, similarity_score=0.6),
        ],
        embedding_run_ref=embedding_run.embedding_run_id,
        index_artifact_ref=space.index_artifact_ref,
        created_at="2026-09-29T03:03:00-05:00",
        metadata={"synthetic_reference": True, "scores_are_illustrative": True},
    )
    return GraphEmbeddingBundle(
        graph_ml_foundation_bundle=foundation,
        runtime_contracts=[runtime],
        embedding_runs=[embedding_run],
        embedding_spaces=[space],
        embeddings=embeddings,
        similarity_queries=[query],
        metadata={
            "purpose": "Platform Core v3.71 synthetic graph embedding reference",
            "synthetic_reference": True,
            "embedding_similarity_is_not_graph_fact": True,
        },
    )


def contract_document() -> dict[str, Any]:
    bundle = reference_graph_embedding_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "extends_contracts": [
            "sc.core.graph-machine-learning-foundation.v1",
            "sc.core.neural-embedding-representation-intelligence.v1",
        ],
        "object_types": [
            "GraphEmbeddingRuntimeContract",
            "GraphEmbeddingSpaceContract",
            "GraphEmbeddingComputationProvenance",
            "GraphEmbeddingObject",
            "GraphSimilarityNeighbor",
            "GraphSimilarityQueryRecord",
            "GraphEmbeddingBundle",
        ],
        "principles": {
            "graph_embedding_is_derived_representation": True,
            "embedding_similarity_is_not_graph_fact": True,
            "embedding_similarity_is_not_evidence": True,
            "embedding_similarity_is_not_identity": True,
            "embedding_distance_is_not_evidence_strength": True,
            "embedding_does_not_establish_relationship": True,
            "embedding_space_is_model_and_snapshot_specific": True,
            "gnn_prediction_is_not_graph_fact": True,
        },
        "capabilities": {
            "node_embedding_objects": True,
            "edge_embedding_objects": True,
            "graph_embedding_objects": True,
            "embedding_space_identity": True,
            "dimension_dtype_normalization_metadata": True,
            "runtime_provider_contracts": True,
            "training_inference_embedding_lineage": True,
            "vector_index_provenance": True,
            "similarity_query_provenance": True,
            "snapshot_bound_embeddings": True,
        },
        "boundaries": {
            "core_computes_graph_embeddings": False,
            "core_builds_vector_indexes": False,
            "core_executes_similarity_search": False,
            "core_installs_graph_embedding_frameworks": False,
            "core_treats_similarity_as_relationship_validation": False,
            "core_treats_nearest_neighbor_as_identity": False,
            "core_mutates_graph_from_similarity": False,
            "runtime_may_mutate_evidence_graph": False,
        },
        "roadmap_integration": {
            "extends_v3700_graph_ml_foundation": True,
            "extends_v3620_neural_embedding_contract": True,
            "prepares_v3720_node_edge_classification_objects": True,
            "prepares_v3730_link_prediction_candidate_relationship_objects": True,
            "prepares_v3740_graph_anomaly_detection": True,
            "prepares_v3750_knowledge_graph_representation_learning": True,
            "prepares_v3760_evidence_graph_neural_analysis_validation_workflow": True,
        },
        "reference": {
            "embedding_space_id": bundle.embedding_spaces[0].embedding_space_id,
            "embedding_count": len(bundle.embeddings),
            "similarity_query_count": len(bundle.similarity_queries),
            "dimensions": bundle.embedding_spaces[0].dimensions,
            "reference_fixture_is_synthetic": True,
            "bundle_fingerprint_sha256": bundle.fingerprint(),
        },
    }
