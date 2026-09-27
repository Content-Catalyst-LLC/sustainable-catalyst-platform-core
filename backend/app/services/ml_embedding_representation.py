from __future__ import annotations

import math
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .ml_explainability_interpretation import (
    MLExplainabilityInterpretationBundle,
    reference_explainability_interpretation_bundle,
)

CORE_RELEASE = "3.62.0"
CONTRACT_VERSION = "sc.core.neural-embedding-representation-intelligence.v1"


def _finite(value: float, label: str) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{label} must be finite")


def _l2(values: list[float]) -> float:
    return math.sqrt(sum(v * v for v in values))


class MLRepresentationModality(str, Enum):
    tabular = "tabular"
    text = "text"
    image = "image"
    audio = "audio"
    graph = "graph"
    time_series = "time-series"
    multimodal = "multimodal"
    other = "other"


class MLSimilarityMetric(str, Enum):
    cosine = "cosine"
    dot_product = "dot-product"
    euclidean = "euclidean"
    manhattan = "manhattan"
    learned = "learned"
    other = "other"


class MLProjectionMethod(str, Enum):
    pca = "pca"
    umap = "umap"
    tsne = "t-sne"
    pacmap = "pacmap"
    custom = "custom"


class MLVectorDType(str, Enum):
    float16 = "float16"
    float32 = "float32"
    float64 = "float64"
    bfloat16 = "bfloat16"


class MLRepresentationModelRecord(BaseModel):
    representation_model_id: str = Field(min_length=2, max_length=500)
    model_spec_ref: str = Field(min_length=2, max_length=500)
    checkpoint_ref: str = Field(min_length=2, max_length=500)
    source_component_ref: str = Field(min_length=2, max_length=500)
    modality: MLRepresentationModality
    output_dimensions: int = Field(ge=1, le=1000000)
    pooling_strategy: str | None = Field(default=None, max_length=240)
    normalization: str | None = Field(default=None, max_length=240)
    runtime_binding_ref: str | None = Field(default=None, max_length=500)
    environment_ref: str | None = Field(default=None, max_length=500)
    model_artifact_ref: str | None = Field(default=None, max_length=1000)
    model_artifact_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    intended_uses: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_model(self):
        if len(self.intended_uses) != len(set(self.intended_uses)):
            raise ValueError("representation intended_uses must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MLEmbeddingSpaceRecord(BaseModel):
    embedding_space_id: str = Field(min_length=2, max_length=500)
    representation_model_ref: str = Field(min_length=2, max_length=500)
    dimensions: int = Field(ge=1, le=1000000)
    dtype: MLVectorDType = MLVectorDType.float32
    similarity_metric: MLSimilarityMetric
    normalized: bool = False
    corpus_ref: str | None = Field(default=None, max_length=1000)
    source_partition_refs: list[str] = Field(default_factory=list)
    index_artifact_ref: str | None = Field(default=None, max_length=1000)
    index_artifact_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    created_by_computation_ref: str | None = Field(default=None, max_length=1000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_space(self):
        if len(self.source_partition_refs) != len(set(self.source_partition_refs)):
            raise ValueError("embedding-space source_partition_refs must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MLEmbeddingObjectRecord(BaseModel):
    embedding_id: str = Field(min_length=2, max_length=500)
    embedding_space_ref: str = Field(min_length=2, max_length=500)
    source_object_ref: str = Field(min_length=2, max_length=1000)
    source_object_type: str = Field(min_length=1, max_length=240)
    source_partition_ref: str | None = Field(default=None, max_length=500)
    dimensions: int = Field(ge=1, le=1000000)
    vector: list[float] | None = None
    vector_artifact_ref: str | None = Field(default=None, max_length=1000)
    vector_artifact_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    l2_norm: float | None = Field(default=None, ge=0.0)
    generated_by_computation_ref: str | None = Field(default=None, max_length=1000)
    created_at: str | None = Field(default=None, max_length=80)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_embedding(self):
        if self.vector is None and self.vector_artifact_ref is None:
            raise ValueError("embedding requires inline vector or vector_artifact_ref")
        if self.vector is not None:
            if len(self.vector) != self.dimensions:
                raise ValueError("embedding vector length must equal dimensions")
            for value in self.vector:
                _finite(value, "embedding vector value")
            actual = _l2(self.vector)
            if self.l2_norm is not None and not math.isclose(actual, self.l2_norm, rel_tol=1e-6, abs_tol=1e-6):
                raise ValueError("embedding l2_norm must match inline vector")
        if self.l2_norm is not None:
            _finite(self.l2_norm, "embedding l2_norm")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MLSimilarityNeighborRecord(BaseModel):
    embedding_ref: str = Field(min_length=2, max_length=500)
    source_object_ref: str = Field(min_length=2, max_length=1000)
    rank: int = Field(ge=1)
    similarity_score: float
    raw_distance: float | None = Field(default=None, ge=0.0)

    @model_validator(mode="after")
    def validate_neighbor(self):
        _finite(self.similarity_score, "similarity score")
        if self.raw_distance is not None:
            _finite(self.raw_distance, "similarity raw_distance")
        return self


class MLSimilarityResultRecord(BaseModel):
    similarity_result_id: str = Field(min_length=2, max_length=500)
    embedding_space_ref: str = Field(min_length=2, max_length=500)
    query_embedding_ref: str = Field(min_length=2, max_length=500)
    metric: MLSimilarityMetric
    neighbors: list[MLSimilarityNeighborRecord] = Field(min_length=1)
    computation_ref: str | None = Field(default=None, max_length=1000)
    index_artifact_ref: str | None = Field(default=None, max_length=1000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_similarity(self):
        refs = [x.embedding_ref for x in self.neighbors]
        ranks = [x.rank for x in self.neighbors]
        if len(refs) != len(set(refs)):
            raise ValueError("similarity neighbor embedding_refs must be unique")
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


class MLProjectionPointRecord(BaseModel):
    embedding_ref: str = Field(min_length=2, max_length=500)
    coordinates: list[float] = Field(min_length=1)
    source_object_ref: str | None = Field(default=None, max_length=1000)
    cluster_ref: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_point(self):
        for value in self.coordinates:
            _finite(value, "projection coordinate")
        return self


class MLVectorProjectionRecord(BaseModel):
    projection_id: str = Field(min_length=2, max_length=500)
    embedding_space_ref: str = Field(min_length=2, max_length=500)
    method: MLProjectionMethod
    input_dimensions: int = Field(ge=1)
    output_dimensions: int = Field(ge=1, le=3)
    points: list[MLProjectionPointRecord] = Field(min_length=2)
    fit_partition_ref: str | None = Field(default=None, max_length=500)
    parameters: dict[str, Any] = Field(default_factory=dict)
    computation_ref: str | None = Field(default=None, max_length=1000)
    artifact_ref: str | None = Field(default=None, max_length=1000)
    artifact_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_projection(self):
        refs = [x.embedding_ref for x in self.points]
        if len(refs) != len(set(refs)):
            raise ValueError("projection embedding_refs must be unique")
        if any(len(x.coordinates) != self.output_dimensions for x in self.points):
            raise ValueError("projection point coordinates must match output_dimensions")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MLRepresentationClusterRecord(BaseModel):
    cluster_id: str = Field(min_length=2, max_length=500)
    embedding_space_ref: str = Field(min_length=2, max_length=500)
    method: str = Field(min_length=1, max_length=240)
    member_embedding_refs: list[str] = Field(min_length=1)
    centroid_embedding_ref: str | None = Field(default=None, max_length=500)
    label: str | None = Field(default=None, max_length=500)
    computation_ref: str | None = Field(default=None, max_length=1000)
    artifact_ref: str | None = Field(default=None, max_length=1000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_cluster(self):
        if len(self.member_embedding_refs) != len(set(self.member_embedding_refs)):
            raise ValueError("cluster member_embedding_refs must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MLRepresentationIntelligenceBundle(BaseModel):
    model_spec_ref: str = Field(min_length=2, max_length=500)
    checkpoint_ref: str = Field(min_length=2, max_length=500)
    explainability_bundle: MLExplainabilityInterpretationBundle
    representation_models: list[MLRepresentationModelRecord] = Field(min_length=1)
    embedding_spaces: list[MLEmbeddingSpaceRecord] = Field(min_length=1)
    embeddings: list[MLEmbeddingObjectRecord] = Field(min_length=1)
    similarity_results: list[MLSimilarityResultRecord] = Field(default_factory=list)
    vector_projections: list[MLVectorProjectionRecord] = Field(default_factory=list)
    clusters: list[MLRepresentationClusterRecord] = Field(default_factory=list)
    explainability_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_bundle(self):
        explain = self.explainability_bundle
        if self.model_spec_ref != explain.model_spec_ref:
            raise ValueError("model_spec_ref must match v3.61 explainability bundle")
        if self.checkpoint_ref != explain.checkpoint_ref:
            raise ValueError("checkpoint_ref must match v3.61 explainability bundle")
        if self.explainability_fingerprint_sha256 != explain.fingerprint():
            raise ValueError("explainability fingerprint must match bundled v3.61 object")

        model_by_id = {x.representation_model_id: x for x in self.representation_models}
        space_by_id = {x.embedding_space_id: x for x in self.embedding_spaces}
        embedding_by_id = {x.embedding_id: x for x in self.embeddings}
        source_to_embedding: dict[str, MLEmbeddingObjectRecord] = {}

        for label, values in (
            ("representation model", list(model_by_id)),
            ("embedding space", list(space_by_id)),
            ("embedding", list(embedding_by_id)),
            ("similarity result", [x.similarity_result_id for x in self.similarity_results]),
            ("projection", [x.projection_id for x in self.vector_projections]),
            ("cluster", [x.cluster_id for x in self.clusters]),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{label} ids must be unique")

        for model in self.representation_models:
            if model.model_spec_ref != self.model_spec_ref:
                raise ValueError("representation model model_spec_ref must match bundle")
            if model.checkpoint_ref != self.checkpoint_ref:
                raise ValueError("representation model checkpoint_ref must match bundle")

        for space in self.embedding_spaces:
            model = model_by_id.get(space.representation_model_ref)
            if model is None:
                raise ValueError("embedding-space representation_model_ref must resolve within bundle")
            if space.dimensions != model.output_dimensions:
                raise ValueError("embedding-space dimensions must match representation model output_dimensions")

        for embedding in self.embeddings:
            space = space_by_id.get(embedding.embedding_space_ref)
            if space is None:
                raise ValueError("embedding embedding_space_ref must resolve within bundle")
            if embedding.dimensions != space.dimensions:
                raise ValueError("embedding dimensions must match embedding space")
            key = f"{embedding.embedding_space_ref}|{embedding.source_object_ref}"
            if key in source_to_embedding:
                raise ValueError("source object may have at most one embedding per embedding space in bundle")
            source_to_embedding[key] = embedding
            if space.normalized and embedding.vector is not None:
                if not math.isclose(_l2(embedding.vector), 1.0, rel_tol=1e-6, abs_tol=1e-6):
                    raise ValueError("inline vector in normalized embedding space must have L2 norm 1")

        for result in self.similarity_results:
            space = space_by_id.get(result.embedding_space_ref)
            if space is None:
                raise ValueError("similarity result embedding_space_ref must resolve within bundle")
            if result.metric != space.similarity_metric:
                raise ValueError("similarity result metric must match embedding space metric")
            query = embedding_by_id.get(result.query_embedding_ref)
            if query is None or query.embedding_space_ref != result.embedding_space_ref:
                raise ValueError("similarity query embedding must resolve in the same embedding space")
            for neighbor in result.neighbors:
                embedded = embedding_by_id.get(neighbor.embedding_ref)
                if embedded is None or embedded.embedding_space_ref != result.embedding_space_ref:
                    raise ValueError("similarity neighbor embedding must resolve in the same embedding space")
                if neighbor.source_object_ref != embedded.source_object_ref:
                    raise ValueError("similarity neighbor source_object_ref must match referenced embedding")

        for projection in self.vector_projections:
            space = space_by_id.get(projection.embedding_space_ref)
            if space is None:
                raise ValueError("projection embedding_space_ref must resolve within bundle")
            if projection.input_dimensions != space.dimensions:
                raise ValueError("projection input_dimensions must match embedding space")
            for point in projection.points:
                embedded = embedding_by_id.get(point.embedding_ref)
                if embedded is None or embedded.embedding_space_ref != projection.embedding_space_ref:
                    raise ValueError("projection embedding_ref must resolve in the same embedding space")
                if point.source_object_ref and point.source_object_ref != embedded.source_object_ref:
                    raise ValueError("projection source_object_ref must match referenced embedding")

        cluster_by_id = {x.cluster_id: x for x in self.clusters}
        for cluster in self.clusters:
            if cluster.embedding_space_ref not in space_by_id:
                raise ValueError("cluster embedding_space_ref must resolve within bundle")
            for ref in cluster.member_embedding_refs:
                embedded = embedding_by_id.get(ref)
                if embedded is None or embedded.embedding_space_ref != cluster.embedding_space_ref:
                    raise ValueError("cluster member must resolve in the same embedding space")
            if cluster.centroid_embedding_ref:
                centroid = embedding_by_id.get(cluster.centroid_embedding_ref)
                if centroid is None or centroid.embedding_space_ref != cluster.embedding_space_ref:
                    raise ValueError("cluster centroid_embedding_ref must resolve in the same embedding space")

        embedding_explanations = explain.embedding_explanations
        if not embedding_explanations:
            raise ValueError("v3.62 reference lineage requires at least one v3.61 embedding explanation")
        for legacy in embedding_explanations:
            model = model_by_id.get(legacy.representation_ref)
            space = space_by_id.get(legacy.embedding_space_ref)
            if model is None:
                raise ValueError("v3.61 representation_ref must resolve to a v3.62 representation model")
            if space is None:
                raise ValueError("v3.61 embedding_space_ref must resolve to a v3.62 embedding space")
            if legacy.dimensions is not None and legacy.dimensions != space.dimensions:
                raise ValueError("v3.61 embedding explanation dimensions must match v3.62 embedding space")
            if legacy.sample_ref:
                query_embedding = source_to_embedding.get(f"{legacy.embedding_space_ref}|{legacy.sample_ref}")
                if query_embedding is None:
                    raise ValueError("v3.61 embedding explanation sample_ref must resolve to a v3.62 embedding object")
                matching = [x for x in self.similarity_results if x.embedding_space_ref == legacy.embedding_space_ref and x.query_embedding_ref == query_embedding.embedding_id]
                if not matching:
                    raise ValueError("v3.61 embedding explanation query must resolve to a v3.62 similarity result")
                result = matching[0]
                ordered = sorted(result.neighbors, key=lambda x: x.rank)
                if len(ordered) < len(legacy.neighbors):
                    raise ValueError("v3.62 similarity result must preserve v3.61 neighbor coverage")
                for old, new in zip(legacy.neighbors, ordered):
                    if old.item_ref != new.source_object_ref or old.rank != new.rank:
                        raise ValueError("v3.61 neighbor refs/ranks must resolve to v3.62 similarity neighbors")
                    if not math.isclose(old.similarity, new.similarity_score, rel_tol=1e-9, abs_tol=1e-9):
                        raise ValueError("v3.61 neighbor similarity must resolve to v3.62 similarity score")
            if legacy.cluster_ref and legacy.cluster_ref not in cluster_by_id:
                raise ValueError("v3.61 cluster_ref must resolve to a v3.62 representation cluster")

        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


def reference_representation_intelligence_bundle() -> MLRepresentationIntelligenceBundle:
    explain = reference_explainability_interpretation_bundle()
    legacy = explain.embedding_explanations[0]
    dims = legacy.dimensions or 16
    model = MLRepresentationModelRecord(
        representation_model_id=legacy.representation_ref,
        model_spec_ref=explain.model_spec_ref,
        checkpoint_ref=explain.checkpoint_ref,
        source_component_ref=legacy.representation_ref,
        modality=MLRepresentationModality.tabular,
        output_dimensions=dims,
        pooling_strategy="penultimate-layer-activation",
        normalization="l2",
        intended_uses=["similarity-analysis", "representation-visualization"],
        limitations=["embedding proximity is model-relative and is not semantic fact"],
    )
    space = MLEmbeddingSpaceRecord(
        embedding_space_id=legacy.embedding_space_ref,
        representation_model_ref=model.representation_model_id,
        dimensions=dims,
        dtype=MLVectorDType.float32,
        similarity_metric=MLSimilarityMetric.cosine,
        normalized=True,
        corpus_ref="corpus:reference-energy:train-validation",
        source_partition_refs=["ml-partition:reference-energy:train", explain.evaluation_bundle.dataset_partition.partition_id],
        index_artifact_ref="artifact:reference-energy:hidden-v1:index",
        index_artifact_sha256="7" * 64,
        created_by_computation_ref="workspace-job:reference-energy:embedding-index:001",
    )
    q = [1.0] + [0.0] * (dims - 1)
    n1 = [0.94, math.sqrt(1.0 - 0.94**2)] + [0.0] * (dims - 2)
    n2 = [0.89, 0.0, math.sqrt(1.0 - 0.89**2)] + [0.0] * (dims - 3)
    n3 = [0.82, 0.0, 0.0, math.sqrt(1.0 - 0.82**2)] + [0.0] * (dims - 4)
    embeddings = [
        MLEmbeddingObjectRecord(embedding_id="embedding:reference-energy:validation:001", embedding_space_ref=space.embedding_space_id, source_object_ref=legacy.sample_ref or "sample:reference-energy:validation:001", source_object_type="sample", source_partition_ref=explain.evaluation_bundle.dataset_partition.partition_id, dimensions=dims, vector=q, l2_norm=1.0, generated_by_computation_ref="workspace-job:reference-energy:embeddings:validation", created_at="2026-09-27T10:00:00Z"),
        MLEmbeddingObjectRecord(embedding_id="embedding:reference-energy:train:117", embedding_space_ref=space.embedding_space_id, source_object_ref=legacy.neighbors[0].item_ref, source_object_type="sample", source_partition_ref="ml-partition:reference-energy:train", dimensions=dims, vector=n1, l2_norm=1.0, generated_by_computation_ref="workspace-job:reference-energy:embeddings:train", created_at="2026-09-27T10:00:00Z"),
        MLEmbeddingObjectRecord(embedding_id="embedding:reference-energy:train:442", embedding_space_ref=space.embedding_space_id, source_object_ref=legacy.neighbors[1].item_ref, source_object_type="sample", source_partition_ref="ml-partition:reference-energy:train", dimensions=dims, vector=n2, l2_norm=1.0, generated_by_computation_ref="workspace-job:reference-energy:embeddings:train", created_at="2026-09-27T10:00:00Z"),
        MLEmbeddingObjectRecord(embedding_id="embedding:reference-energy:train:509", embedding_space_ref=space.embedding_space_id, source_object_ref="sample:reference-energy:train:509", source_object_type="sample", source_partition_ref="ml-partition:reference-energy:train", dimensions=dims, vector=n3, l2_norm=1.0, generated_by_computation_ref="workspace-job:reference-energy:embeddings:train", created_at="2026-09-27T10:00:00Z"),
    ]
    similarity = MLSimilarityResultRecord(
        similarity_result_id="ml-similarity:reference-energy:validation:001",
        embedding_space_ref=space.embedding_space_id,
        query_embedding_ref=embeddings[0].embedding_id,
        metric=MLSimilarityMetric.cosine,
        neighbors=[
            MLSimilarityNeighborRecord(embedding_ref=embeddings[1].embedding_id, source_object_ref=embeddings[1].source_object_ref, rank=1, similarity_score=legacy.neighbors[0].similarity, raw_distance=1.0-legacy.neighbors[0].similarity),
            MLSimilarityNeighborRecord(embedding_ref=embeddings[2].embedding_id, source_object_ref=embeddings[2].source_object_ref, rank=2, similarity_score=legacy.neighbors[1].similarity, raw_distance=1.0-legacy.neighbors[1].similarity),
            MLSimilarityNeighborRecord(embedding_ref=embeddings[3].embedding_id, source_object_ref=embeddings[3].source_object_ref, rank=3, similarity_score=0.82, raw_distance=0.18),
        ],
        computation_ref="workspace-job:reference-energy:similarity:001",
        index_artifact_ref=space.index_artifact_ref,
    )
    cluster = MLRepresentationClusterRecord(
        cluster_id=legacy.cluster_ref or "cluster:reference-energy:hidden:3",
        embedding_space_ref=space.embedding_space_id,
        method="reference-density-cluster",
        member_embedding_refs=[x.embedding_id for x in embeddings],
        label="similar-energy-weather-regime",
        computation_ref="workspace-job:reference-energy:representation-clusters:001",
    )
    projection = MLVectorProjectionRecord(
        projection_id="ml-projection:reference-energy:hidden-v1:pca2",
        embedding_space_ref=space.embedding_space_id,
        method=MLProjectionMethod.pca,
        input_dimensions=dims,
        output_dimensions=2,
        points=[
            MLProjectionPointRecord(embedding_ref=embeddings[0].embedding_id, source_object_ref=embeddings[0].source_object_ref, coordinates=[0.08, 0.02], cluster_ref=cluster.cluster_id),
            MLProjectionPointRecord(embedding_ref=embeddings[1].embedding_id, source_object_ref=embeddings[1].source_object_ref, coordinates=[0.11, 0.06], cluster_ref=cluster.cluster_id),
            MLProjectionPointRecord(embedding_ref=embeddings[2].embedding_id, source_object_ref=embeddings[2].source_object_ref, coordinates=[0.16, -0.04], cluster_ref=cluster.cluster_id),
            MLProjectionPointRecord(embedding_ref=embeddings[3].embedding_id, source_object_ref=embeddings[3].source_object_ref, coordinates=[0.21, 0.09], cluster_ref=cluster.cluster_id),
        ],
        fit_partition_ref="ml-partition:reference-energy:train",
        parameters={"components": 2},
        computation_ref="workspace-job:reference-energy:projection:001",
        artifact_ref=legacy.projection_artifact_ref,
        artifact_sha256=legacy.projection_artifact_sha256,
    )
    return MLRepresentationIntelligenceBundle(
        model_spec_ref=explain.model_spec_ref,
        checkpoint_ref=explain.checkpoint_ref,
        explainability_bundle=explain,
        representation_models=[model],
        embedding_spaces=[space],
        embeddings=embeddings,
        similarity_results=[similarity],
        vector_projections=[projection],
        clusters=[cluster],
        explainability_fingerprint_sha256=explain.fingerprint(),
    )


def contract_document() -> dict[str, Any]:
    ref = reference_representation_intelligence_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "object_types": [
            "MLRepresentationModelRecord",
            "MLEmbeddingSpaceRecord",
            "MLEmbeddingObjectRecord",
            "MLSimilarityNeighborRecord",
            "MLSimilarityResultRecord",
            "MLProjectionPointRecord",
            "MLVectorProjectionRecord",
            "MLRepresentationClusterRecord",
            "MLRepresentationIntelligenceBundle",
        ],
        "representation_capabilities": {
            "representation_models": True,
            "embedding_spaces": True,
            "source_bound_embedding_objects": True,
            "similarity_results": True,
            "vector_projections": True,
            "representation_clusters": True,
            "inline_or_artifact_vectors": True,
            "cross_product_representation_refs": True,
        },
        "integration": {
            "extends_explainability_model_interpretation_v3610": True,
            "resolves_v361_embedding_representation_refs": True,
            "resolves_v361_embedding_space_refs": True,
            "preserves_v361_explainability_fingerprint": True,
            "retains_v359_dataset_partition_lineage": True,
            "links_model_specification_and_checkpoint": True,
            "workspace_remains_default_compute_host": True,
            "lab_remains_experiment_host": True,
            "library_librarian_graph_and_site_products_can_consume": True,
        },
        "reproducibility": {
            "deterministic_bundle_fingerprint": True,
            "representation_model_checkpoint_binding": True,
            "embedding_vector_artifact_hashes_supported": True,
            "embedding_index_hashes_supported": True,
            "source_object_binding_required": True,
            "projection_artifact_hashes_supported": True,
            "similarity_query_and_neighbor_resolution_required": True,
            "normalized_space_vector_norm_validation": True,
        },
        "governance": {
            "embedding_is_derived_analytical_representation_not_evidence": True,
            "embedding_similarity_is_not_semantic_fact": True,
            "nearest_neighbor_is_not_relationship_fact": True,
            "projection_distance_is_not_original_space_distance": True,
            "cluster_membership_is_analytical_not_ground_truth": True,
            "representation_objects_require_source_lineage": True,
            "learned_representation_does_not_replace_source_evidence": True,
        },
        "boundaries": {
            "core_computes_embeddings": False,
            "core_downloads_representation_models": False,
            "core_builds_vector_indexes": False,
            "core_runs_similarity_search": False,
            "core_projects_vectors": False,
            "core_clusters_embeddings": False,
            "core_trains_representation_models": False,
            "core_promotes_neighbors_to_evidence": False,
            "core_infers_relationship_facts_from_proximity": False,
            "core_treats_embedding_similarity_as_semantic_truth": False,
            "core_certifies_representation_quality": False,
        },
        "reference": {
            "representation_model_id": ref.representation_models[0].representation_model_id,
            "embedding_space_id": ref.embedding_spaces[0].embedding_space_id,
            "query_embedding_id": ref.similarity_results[0].query_embedding_ref,
            "similarity_result_id": ref.similarity_results[0].similarity_result_id,
            "projection_id": ref.vector_projections[0].projection_id,
            "cluster_id": ref.clusters[0].cluster_id,
            "bundle_fingerprint_sha256": ref.fingerprint(),
        },
    }
