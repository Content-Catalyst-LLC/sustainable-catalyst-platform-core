from __future__ import annotations

import math
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .graph_anomaly_detection import GraphAnomalyDetectionBundle, reference_graph_anomaly_detection_bundle
from .graph_machine_learning import GraphMLTaskKind
from .machine_learning_models import ExecutionHost

CORE_RELEASE = "3.75.0"
CONTRACT_VERSION = "sc.core.knowledge-graph-representation-learning.v1"


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


def _finite(value: float, label: str) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{label} must be finite")


class KGRepresentationObjective(str, Enum):
    translational = "translational"
    bilinear = "bilinear"
    complex = "complex"
    rotational = "rotational"
    graph_neural = "graph-neural"
    hybrid = "hybrid"


class KGRepresentationTargetKind(str, Enum):
    entity = "entity"
    relation = "relation"


class KGScoreDirection(str, Enum):
    higher_is_better = "higher-is-better"
    lower_is_better = "lower-is-better"


class KGNegativeSamplingStrategy(str, Enum):
    corrupt_head = "corrupt-head"
    corrupt_tail = "corrupt-tail"
    corrupt_both = "corrupt-both"
    type_constrained = "type-constrained"
    adversarial = "adversarial"
    custom = "custom"


class KGEvaluationProtocol(str, Enum):
    raw = "raw"
    filtered = "filtered"
    time_aware = "time-aware"


class KnowledgeGraphRepresentationTask(BaseModel):
    kg_representation_task_id: str = Field(min_length=2, max_length=500)
    graph_ml_task_kind: Literal[GraphMLTaskKind.representation_learning] = GraphMLTaskKind.representation_learning
    snapshot_ref: str = Field(min_length=2, max_length=500)
    model_ref: str = Field(min_length=2, max_length=500)
    objectives: list[KGRepresentationObjective] = Field(min_length=1)
    entity_refs: list[str] = Field(min_length=2)
    relationship_types: list[str] = Field(min_length=1)
    feature_binding_refs: list[str] = Field(default_factory=list)
    graph_embedding_space_refs: list[str] = Field(default_factory=list)
    negative_sampling_policy_ref: str = Field(min_length=2, max_length=500)
    leakage_control_refs: list[str] = Field(default_factory=list)
    task_definition_is_not_evidence: Literal[True] = True
    task_does_not_assert_missing_links: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_task(self):
        for xs, label in (([x.value for x in self.objectives], "objectives"), (self.entity_refs, "entity_refs"), (self.relationship_types, "relationship_types"), (self.feature_binding_refs, "feature_binding_refs"), (self.graph_embedding_space_refs, "graph_embedding_space_refs"), (self.leakage_control_refs, "leakage_control_refs")):
            _unique(xs, label)
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class KnowledgeGraphRepresentationRuntimeContract(BaseModel):
    kg_runtime_contract_id: str = Field(min_length=2, max_length=500)
    extends_graph_ml_runtime_ref: str = Field(min_length=2, max_length=500)
    execution_host: ExecutionHost
    framework: str = Field(min_length=1, max_length=240)
    framework_version: str | None = Field(default=None, max_length=120)
    supported_objectives: list[KGRepresentationObjective] = Field(min_length=1)
    supports_negative_sampling: bool = True
    supports_entity_embeddings: bool = True
    supports_relation_embeddings: bool = True
    supports_triple_scoring: bool = True
    core_executes_kg_representation_learning: Literal[False] = False
    runtime_may_mutate_evidence_graph: Literal[False] = False
    runtime_may_promote_scored_triple: Literal[False] = False
    arbitrary_code_allowed_by_core: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_runtime(self):
        _unique([x.value for x in self.supported_objectives], "supported_objectives")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class KGScoringFunctionContract(BaseModel):
    scoring_function_id: str = Field(min_length=2, max_length=500)
    family: KGRepresentationObjective
    name: str = Field(min_length=1, max_length=240)
    score_direction: KGScoreDirection
    score_is_probability: bool = False
    score_is_not_evidence_strength: Literal[True] = True
    score_does_not_establish_relationship: Literal[True] = True
    parameters: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class KGNegativeSamplingPolicy(BaseModel):
    negative_sampling_policy_id: str = Field(min_length=2, max_length=500)
    snapshot_ref: str = Field(min_length=2, max_length=500)
    strategy: KGNegativeSamplingStrategy
    positive_evidence_edge_refs: list[str] = Field(min_length=1)
    candidate_entity_refs: list[str] = Field(min_length=2)
    relationship_types: list[str] = Field(min_length=1)
    samples_per_positive: int = Field(ge=1, le=100000)
    random_seed: int | None = None
    filtered_against_known_evidence_edges: Literal[True] = True
    absent_edge_is_not_false_fact: Literal[True] = True
    negative_samples_are_training_artifacts: Literal[True] = True
    negative_samples_may_not_be_written_as_evidence: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_policy(self):
        for xs, label in ((self.positive_evidence_edge_refs, "positive_evidence_edge_refs"), (self.candidate_entity_refs, "candidate_entity_refs"), (self.relationship_types, "relationship_types")):
            _unique(xs, label)
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class KGRepresentationSpaceContract(BaseModel):
    kg_representation_space_id: str = Field(min_length=2, max_length=500)
    snapshot_ref: str = Field(min_length=2, max_length=500)
    task_ref: str = Field(min_length=2, max_length=500)
    model_ref: str = Field(min_length=2, max_length=500)
    runtime_contract_ref: str = Field(min_length=2, max_length=500)
    scoring_function_ref: str = Field(min_length=2, max_length=500)
    dimensions: int = Field(ge=1, le=1000000)
    entity_space_enabled: bool = True
    relation_space_enabled: bool = True
    normalized: bool = False
    training_run_ref: str = Field(min_length=2, max_length=500)
    checkpoint_ref: str | None = Field(default=None, max_length=1000)
    representation_space_is_model_and_snapshot_specific: Literal[True] = True
    representation_similarity_is_not_graph_fact: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class KGRepresentationVector(BaseModel):
    kg_vector_id: str = Field(min_length=2, max_length=500)
    representation_space_ref: str = Field(min_length=2, max_length=500)
    target_kind: KGRepresentationTargetKind
    target_ref: str = Field(min_length=1, max_length=1000)
    dimensions: int = Field(ge=1, le=1000000)
    vector: list[float] | None = None
    vector_artifact_ref: str | None = Field(default=None, max_length=1000)
    vector_artifact_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    generated_by_training_run_ref: str = Field(min_length=2, max_length=500)
    is_graph_fact: Literal[False] = False
    is_evidence: Literal[False] = False
    representation_does_not_establish_identity_or_relationship: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_vector(self):
        if self.vector is None and self.vector_artifact_ref is None:
            raise ValueError("KG representation vector requires inline vector or vector_artifact_ref")
        if self.vector_artifact_sha256 and not self.vector_artifact_ref:
            raise ValueError("vector_artifact_sha256 requires vector_artifact_ref")
        if self.vector is not None:
            if len(self.vector) != self.dimensions:
                raise ValueError("KG representation vector length must equal dimensions")
            for value in self.vector:
                _finite(value, "KG representation vector value")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class KGRepresentationTrainingProvenance(BaseModel):
    kg_training_provenance_id: str = Field(min_length=2, max_length=500)
    graph_ml_training_run_ref: str = Field(min_length=2, max_length=500)
    task_ref: str = Field(min_length=2, max_length=500)
    runtime_contract_ref: str = Field(min_length=2, max_length=500)
    model_ref: str = Field(min_length=2, max_length=500)
    scoring_function_ref: str = Field(min_length=2, max_length=500)
    negative_sampling_policy_ref: str = Field(min_length=2, max_length=500)
    loss_function: str = Field(min_length=1, max_length=300)
    optimizer: str | None = Field(default=None, max_length=300)
    training_data_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    checkpoint_ref: str | None = Field(default=None, max_length=1000)
    hyperparameters: dict[str, Any] = Field(default_factory=dict)
    output_artifact_refs: list[str] = Field(min_length=1)
    training_output_is_derived_representation: Literal[True] = True
    training_does_not_create_graph_facts: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_training(self):
        _unique(self.output_artifact_refs, "output_artifact_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class KGTripleScoreRecord(BaseModel):
    triple_score_id: str = Field(min_length=2, max_length=500)
    representation_space_ref: str = Field(min_length=2, max_length=500)
    scoring_function_ref: str = Field(min_length=2, max_length=500)
    inference_run_ref: str = Field(min_length=2, max_length=500)
    subject_node_ref: str = Field(min_length=2, max_length=1000)
    relationship_type: str = Field(min_length=1, max_length=300)
    object_node_ref: str = Field(min_length=2, max_length=1000)
    raw_score: float
    probability: float | None = Field(default=None, ge=0.0, le=1.0)
    rank: int | None = Field(default=None, ge=1)
    known_evidence_edge_ref: str | None = Field(default=None, max_length=1000)
    candidate_relationship_ref: str | None = Field(default=None, max_length=1000)
    source_entity_vector_refs: list[str] = Field(min_length=2, max_length=2)
    relation_vector_ref: str = Field(min_length=2, max_length=500)
    is_graph_fact: Literal[False] = False
    is_evidence: Literal[False] = False
    score_is_not_evidence_strength: Literal[True] = True
    scored_triple_does_not_establish_relationship: Literal[True] = True
    separate_validation_required_for_candidate_or_evidence_use: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_score(self):
        if self.subject_node_ref == self.object_node_ref:
            raise ValueError("KG triple score cannot use identical subject/object in this contract")
        _finite(self.raw_score, "KG triple raw_score")
        _unique(self.source_entity_vector_refs, "source_entity_vector_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class KGRankingEvaluationRecord(BaseModel):
    kg_ranking_evaluation_id: str = Field(min_length=2, max_length=500)
    task_ref: str = Field(min_length=2, max_length=500)
    representation_space_ref: str = Field(min_length=2, max_length=500)
    evaluation_run_ref: str = Field(min_length=2, max_length=500)
    dataset_partition_ref: str = Field(min_length=2, max_length=1000)
    protocol: KGEvaluationProtocol
    metric_values: dict[str, float] = Field(min_length=1)
    known_positive_filter_ref: str | None = Field(default=None, max_length=1000)
    evaluation_metrics_are_descriptive_not_evidence: Literal[True] = True
    ranking_performance_does_not_establish_graph_truth: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_eval(self):
        for key, value in self.metric_values.items():
            if not key:
                raise ValueError("KG evaluation metric name required")
            _finite(value, "KG evaluation metric")
        if self.protocol == KGEvaluationProtocol.filtered and not self.known_positive_filter_ref:
            raise ValueError("filtered KG ranking evaluation requires known_positive_filter_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class KnowledgeGraphRepresentationLearningBundle(BaseModel):
    graph_anomaly_detection_bundle: GraphAnomalyDetectionBundle
    tasks: list[KnowledgeGraphRepresentationTask] = Field(min_length=1)
    runtime_contracts: list[KnowledgeGraphRepresentationRuntimeContract] = Field(min_length=1)
    scoring_functions: list[KGScoringFunctionContract] = Field(min_length=1)
    negative_sampling_policies: list[KGNegativeSamplingPolicy] = Field(min_length=1)
    representation_spaces: list[KGRepresentationSpaceContract] = Field(min_length=1)
    vectors: list[KGRepresentationVector] = Field(min_length=1)
    training_provenance: list[KGRepresentationTrainingProvenance] = Field(min_length=1)
    triple_scores: list[KGTripleScoreRecord] = Field(min_length=1)
    evaluations: list[KGRankingEvaluationRecord] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_bundle(self):
        groups = (
            (self.tasks, "tasks", "kg_representation_task_id"),
            (self.runtime_contracts, "runtime_contracts", "kg_runtime_contract_id"),
            (self.scoring_functions, "scoring_functions", "scoring_function_id"),
            (self.negative_sampling_policies, "negative_sampling_policies", "negative_sampling_policy_id"),
            (self.representation_spaces, "representation_spaces", "kg_representation_space_id"),
            (self.vectors, "vectors", "kg_vector_id"),
            (self.training_provenance, "training_provenance", "kg_training_provenance_id"),
            (self.triple_scores, "triple_scores", "triple_score_id"),
            (self.evaluations, "evaluations", "kg_ranking_evaluation_id"),
        )
        for xs, label, attr in groups:
            _unique([getattr(x, attr) for x in xs], label)

        anomaly = self.graph_anomaly_detection_bundle
        lp = anomaly.graph_link_prediction_bundle
        gb = lp.graph_classification_bundle.graph_embedding_bundle
        graph = gb.graph_ml_foundation_bundle
        snapshots = {x.snapshot_id: x for x in graph.snapshots}
        graph_runtime_ids = {x.runtime_contract_id for x in graph.runtime_contracts}
        graph_model_ids = {x.foundation_id for x in graph.model_foundations}
        graph_model_spec_ids = {x.model_spec.model_spec_id for x in graph.model_foundations}
        run_ids = {x.run_id for x in graph.run_provenance}
        feature_ids = {x.feature_binding_id for x in graph.feature_bindings}
        graph_embedding_space_ids = {x.embedding_space_id for x in gb.embedding_spaces}
        candidate_ids = {x.candidate_relationship_id for x in lp.candidate_relationships}
        tasks = {x.kg_representation_task_id: x for x in self.tasks}
        runtimes = {x.kg_runtime_contract_id: x for x in self.runtime_contracts}
        scorers = {x.scoring_function_id: x for x in self.scoring_functions}
        policies = {x.negative_sampling_policy_id: x for x in self.negative_sampling_policies}
        spaces = {x.kg_representation_space_id: x for x in self.representation_spaces}
        vectors = {x.kg_vector_id: x for x in self.vectors}
        trainings = {x.kg_training_provenance_id: x for x in self.training_provenance}

        for task in self.tasks:
            if task.snapshot_ref not in snapshots:
                raise ValueError("KG representation task snapshot must resolve")
            snap = snapshots[task.snapshot_ref]
            if any(x not in snap.node_refs for x in task.entity_refs):
                raise ValueError("KG task entity_refs must resolve to snapshot nodes")
            if task.model_ref not in graph_model_ids and task.model_ref not in graph_model_spec_ids:
                raise ValueError("KG task model_ref must resolve")
            if any(x not in feature_ids for x in task.feature_binding_refs):
                raise ValueError("KG task feature refs must resolve")
            if any(x not in graph_embedding_space_ids for x in task.graph_embedding_space_refs):
                raise ValueError("KG task graph embedding spaces must resolve")
            if task.negative_sampling_policy_ref not in policies:
                raise ValueError("KG task negative sampling policy must resolve")

        for runtime in self.runtime_contracts:
            if runtime.extends_graph_ml_runtime_ref not in graph_runtime_ids:
                raise ValueError("KG runtime must extend graph ML runtime")

        for policy in self.negative_sampling_policies:
            if policy.snapshot_ref not in snapshots:
                raise ValueError("KG negative sampling snapshot must resolve")
            snap = snapshots[policy.snapshot_ref]
            edge_ids = {x.evidence_edge_ref for x in snap.evidence_edges}
            if any(x not in edge_ids for x in policy.positive_evidence_edge_refs):
                raise ValueError("KG positive evidence edge refs must resolve")
            if any(x not in snap.node_refs for x in policy.candidate_entity_refs):
                raise ValueError("KG candidate entities must resolve")

        for space in self.representation_spaces:
            if space.snapshot_ref not in snapshots or space.task_ref not in tasks or space.runtime_contract_ref not in runtimes or space.scoring_function_ref not in scorers:
                raise ValueError("KG representation space references must resolve")
            if space.training_run_ref not in run_ids:
                raise ValueError("KG representation space training run must resolve")

        entity_vector_targets: dict[str, str] = {}
        relation_vector_targets: dict[str, str] = {}
        for vector in self.vectors:
            if vector.representation_space_ref not in spaces:
                raise ValueError("KG vector representation space must resolve")
            space = spaces[vector.representation_space_ref]
            if vector.dimensions != space.dimensions:
                raise ValueError("KG vector dimensions must match representation space")
            if vector.generated_by_training_run_ref not in run_ids:
                raise ValueError("KG vector training run must resolve")
            snap = snapshots[space.snapshot_ref]
            task = tasks[space.task_ref]
            if vector.target_kind == KGRepresentationTargetKind.entity:
                if vector.target_ref not in snap.node_refs:
                    raise ValueError("KG entity vector target must resolve to snapshot node")
                entity_vector_targets[vector.kg_vector_id] = vector.target_ref
            else:
                if vector.target_ref not in task.relationship_types:
                    raise ValueError("KG relation vector target must resolve to task relationship type")
                relation_vector_targets[vector.kg_vector_id] = vector.target_ref

        for training in self.training_provenance:
            if training.graph_ml_training_run_ref not in run_ids or training.task_ref not in tasks or training.runtime_contract_ref not in runtimes or training.scoring_function_ref not in scorers or training.negative_sampling_policy_ref not in policies:
                raise ValueError("KG training provenance references must resolve")

        for score in self.triple_scores:
            if score.representation_space_ref not in spaces or score.scoring_function_ref not in scorers or score.inference_run_ref not in run_ids:
                raise ValueError("KG triple score references must resolve")
            space = spaces[score.representation_space_ref]
            snap = snapshots[space.snapshot_ref]
            task = tasks[space.task_ref]
            if score.subject_node_ref not in snap.node_refs or score.object_node_ref not in snap.node_refs:
                raise ValueError("KG triple score endpoints must resolve")
            if score.relationship_type not in task.relationship_types:
                raise ValueError("KG triple relationship type must be declared by task")
            if any(x not in entity_vector_targets for x in score.source_entity_vector_refs):
                raise ValueError("KG triple entity vector refs must resolve")
            if entity_vector_targets[score.source_entity_vector_refs[0]] != score.subject_node_ref or entity_vector_targets[score.source_entity_vector_refs[1]] != score.object_node_ref:
                raise ValueError("KG triple entity vectors must match subject/object")
            if score.relation_vector_ref not in relation_vector_targets or relation_vector_targets[score.relation_vector_ref] != score.relationship_type:
                raise ValueError("KG triple relation vector must match relationship type")
            if score.known_evidence_edge_ref:
                edge = next((x for x in snap.evidence_edges if x.evidence_edge_ref == score.known_evidence_edge_ref), None)
                if edge is None:
                    raise ValueError("known evidence edge ref must resolve")
                if (edge.source_node_ref, edge.relationship_type, edge.target_node_ref) != (score.subject_node_ref, score.relationship_type, score.object_node_ref):
                    raise ValueError("known evidence edge must match scored triple")
            if score.candidate_relationship_ref and score.candidate_relationship_ref not in candidate_ids:
                raise ValueError("candidate relationship ref must resolve")
            scorer = scorers[score.scoring_function_ref]
            if scorer.score_is_probability and score.probability is None:
                raise ValueError("probabilistic KG scoring function requires probability")

        for evaluation in self.evaluations:
            if evaluation.task_ref not in tasks or evaluation.representation_space_ref not in spaces:
                raise ValueError("KG ranking evaluation references must resolve")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


def reference_knowledge_graph_representation_learning_bundle() -> KnowledgeGraphRepresentationLearningBundle:
    anomaly = reference_graph_anomaly_detection_bundle()
    lp = anomaly.graph_link_prediction_bundle
    gb = lp.graph_classification_bundle.graph_embedding_bundle
    graph = gb.graph_ml_foundation_bundle
    snap = graph.snapshots[0]
    feature = graph.feature_bindings[0]
    train_run = graph.run_provenance[0]
    infer_run = graph.run_provenance[1]
    relation_types = [snap.evidence_edges[0].relationship_type, lp.tasks[0].allowed_relationship_types[0]]

    policy = KGNegativeSamplingPolicy(
        negative_sampling_policy_id="kg-negative-sampling:reference:v1",
        snapshot_ref=snap.snapshot_id,
        strategy=KGNegativeSamplingStrategy.type_constrained,
        positive_evidence_edge_refs=[snap.evidence_edges[0].evidence_edge_ref],
        candidate_entity_refs=snap.node_refs,
        relationship_types=relation_types,
        samples_per_positive=4,
        random_seed=3750,
        metadata={"synthetic_reference": True},
    )
    task = KnowledgeGraphRepresentationTask(
        kg_representation_task_id="kg-representation-task:reference:v1",
        snapshot_ref=snap.snapshot_id,
        model_ref=graph.model_foundations[0].foundation_id,
        objectives=[KGRepresentationObjective.translational, KGRepresentationObjective.graph_neural],
        entity_refs=snap.node_refs,
        relationship_types=relation_types,
        feature_binding_refs=[feature.feature_binding_id],
        graph_embedding_space_refs=[gb.embedding_spaces[0].embedding_space_id],
        negative_sampling_policy_ref=policy.negative_sampling_policy_id,
        leakage_control_refs=["control:reference:known-positive-filter:v1"],
        metadata={"synthetic_reference": True, "knowledge_graph_specific": True},
    )
    runtime = KnowledgeGraphRepresentationRuntimeContract(
        kg_runtime_contract_id="kg-representation-runtime:reference:v1",
        extends_graph_ml_runtime_ref=graph.runtime_contracts[0].runtime_contract_id,
        execution_host=ExecutionHost.workspace,
        framework="pytorch-geometric-kg-compatible",
        framework_version="external",
        supported_objectives=[KGRepresentationObjective.translational, KGRepresentationObjective.graph_neural],
        metadata={"synthetic_reference": True, "workspace_computes": True},
    )
    scorer = KGScoringFunctionContract(
        scoring_function_id="kg-scoring-function:reference:translational:v1",
        family=KGRepresentationObjective.translational,
        name="reference-translational-distance",
        score_direction=KGScoreDirection.lower_is_better,
        score_is_probability=False,
        parameters={"norm": "l2"},
        metadata={"synthetic_reference": True},
    )
    space = KGRepresentationSpaceContract(
        kg_representation_space_id="kg-representation-space:reference:v1",
        snapshot_ref=snap.snapshot_id,
        task_ref=task.kg_representation_task_id,
        model_ref=task.model_ref,
        runtime_contract_ref=runtime.kg_runtime_contract_id,
        scoring_function_ref=scorer.scoring_function_id,
        dimensions=4,
        training_run_ref=train_run.run_id,
        checkpoint_ref="artifact:reference:kg-representation-checkpoint:v1",
        metadata={"synthetic_reference": True},
    )
    entity_vectors = [
        KGRepresentationVector(kg_vector_id="kg-vector:entity:en:v1", representation_space_ref=space.kg_representation_space_id, target_kind=KGRepresentationTargetKind.entity, target_ref=snap.node_refs[0], dimensions=4, vector=[0.10,0.20,0.30,0.40], generated_by_training_run_ref=train_run.run_id),
        KGRepresentationVector(kg_vector_id="kg-vector:entity:zh:v1", representation_space_ref=space.kg_representation_space_id, target_kind=KGRepresentationTargetKind.entity, target_ref=snap.node_refs[1], dimensions=4, vector=[0.12,0.19,0.31,0.39], generated_by_training_run_ref=train_run.run_id),
        KGRepresentationVector(kg_vector_id="kg-vector:entity:es:v1", representation_space_ref=space.kg_representation_space_id, target_kind=KGRepresentationTargetKind.entity, target_ref=snap.node_refs[2], dimensions=4, vector=[0.11,0.18,0.29,0.43], generated_by_training_run_ref=train_run.run_id),
    ]
    relation_vectors = [
        KGRepresentationVector(kg_vector_id="kg-vector:relation:cooccurs:v1", representation_space_ref=space.kg_representation_space_id, target_kind=KGRepresentationTargetKind.relation, target_ref=relation_types[0], dimensions=4, vector=[0.02,-0.01,0.01,-0.02], generated_by_training_run_ref=train_run.run_id),
        KGRepresentationVector(kg_vector_id="kg-vector:relation:semantic-related:v1", representation_space_ref=space.kg_representation_space_id, target_kind=KGRepresentationTargetKind.relation, target_ref=relation_types[1], dimensions=4, vector=[0.03,0.00,-0.02,0.01], generated_by_training_run_ref=train_run.run_id),
    ]
    training = KGRepresentationTrainingProvenance(
        kg_training_provenance_id="kg-training-provenance:reference:v1",
        graph_ml_training_run_ref=train_run.run_id,
        task_ref=task.kg_representation_task_id,
        runtime_contract_ref=runtime.kg_runtime_contract_id,
        model_ref=task.model_ref,
        scoring_function_ref=scorer.scoring_function_id,
        negative_sampling_policy_ref=policy.negative_sampling_policy_id,
        loss_function="margin-ranking-loss",
        optimizer="adam-compatible",
        training_data_fingerprint_sha256=snap.fingerprint(),
        checkpoint_ref=space.checkpoint_ref,
        hyperparameters={"margin": 1.0, "epochs": 4},
        output_artifact_refs=[space.checkpoint_ref, "artifact:reference:kg-entity-relation-vectors:v1"],
        metadata={"synthetic_reference": True},
    )
    known_score = KGTripleScoreRecord(
        triple_score_id="kg-triple-score:reference:known-edge:v1",
        representation_space_ref=space.kg_representation_space_id,
        scoring_function_ref=scorer.scoring_function_id,
        inference_run_ref=infer_run.run_id,
        subject_node_ref=snap.node_refs[0], relationship_type=relation_types[0], object_node_ref=snap.node_refs[1],
        raw_score=0.12, rank=1,
        known_evidence_edge_ref=snap.evidence_edges[0].evidence_edge_ref,
        source_entity_vector_refs=[entity_vectors[0].kg_vector_id,entity_vectors[1].kg_vector_id],
        relation_vector_ref=relation_vectors[0].kg_vector_id,
        metadata={"synthetic_reference": True, "known_edge_score_is_descriptive": True},
    )
    candidate = lp.candidate_relationships[0]
    candidate_score = KGTripleScoreRecord(
        triple_score_id="kg-triple-score:reference:candidate:v1",
        representation_space_ref=space.kg_representation_space_id,
        scoring_function_ref=scorer.scoring_function_id,
        inference_run_ref=infer_run.run_id,
        subject_node_ref=candidate.source_node_ref, relationship_type=candidate.relationship_type_candidate, object_node_ref=candidate.target_node_ref,
        raw_score=0.21, rank=2,
        candidate_relationship_ref=candidate.candidate_relationship_id,
        source_entity_vector_refs=[entity_vectors[0].kg_vector_id,entity_vectors[2].kg_vector_id],
        relation_vector_ref=relation_vectors[1].kg_vector_id,
        metadata={"synthetic_reference": True, "candidate_remains_non_evidentiary": True},
    )
    evaluation = KGRankingEvaluationRecord(
        kg_ranking_evaluation_id="kg-ranking-evaluation:reference:v1",
        task_ref=task.kg_representation_task_id,
        representation_space_ref=space.kg_representation_space_id,
        evaluation_run_ref="kg-evaluation-run:reference:v1",
        dataset_partition_ref="dataset-partition:reference:kg-heldout:v1",
        protocol=KGEvaluationProtocol.filtered,
        metric_values={"mrr":0.71,"hits_at_1":0.62,"hits_at_10":0.91},
        known_positive_filter_ref="filter:reference:known-positive-triples:v1",
        metadata={"synthetic_reference": True},
    )
    return KnowledgeGraphRepresentationLearningBundle(
        graph_anomaly_detection_bundle=anomaly,
        tasks=[task], runtime_contracts=[runtime], scoring_functions=[scorer],
        negative_sampling_policies=[policy], representation_spaces=[space],
        vectors=entity_vectors+relation_vectors, training_provenance=[training],
        triple_scores=[known_score,candidate_score], evaluations=[evaluation],
        metadata={"reference_fixture":"synthetic-contract-fixture","representation_scores_are_not_evidence":True,"gnn_prediction_is_not_graph_fact":True},
    )


def contract_document() -> dict[str, Any]:
    b = reference_knowledge_graph_representation_learning_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "extends_contracts": [
            "sc.core.graph-machine-learning-foundation.v1",
            "sc.core.graph-embedding-runtime.v1",
            "sc.core.graph-node-edge-classification.v1",
            "sc.core.graph-link-prediction-candidate-relationship.v1",
            "sc.core.graph-anomaly-detection.v1",
        ],
        "object_types": [
            "KnowledgeGraphRepresentationTask",
            "KnowledgeGraphRepresentationRuntimeContract",
            "KGScoringFunctionContract",
            "KGNegativeSamplingPolicy",
            "KGRepresentationSpaceContract",
            "KGRepresentationVector",
            "KGRepresentationTrainingProvenance",
            "KGTripleScoreRecord",
            "KGRankingEvaluationRecord",
            "KnowledgeGraphRepresentationLearningBundle",
        ],
        "principles": {
            "knowledge_graph_representation_is_derived_model_output": True,
            "entity_embedding_is_not_entity_identity": True,
            "relation_embedding_is_not_relationship_fact": True,
            "triple_score_is_not_graph_fact": True,
            "triple_score_is_not_evidence": True,
            "triple_score_is_not_evidence_strength": True,
            "high_triple_score_does_not_establish_relationship": True,
            "negative_sample_is_not_false_fact": True,
            "absent_edge_is_not_negative_evidence": True,
            "ranking_metric_is_not_truth_measure": True,
            "candidate_relationship_remains_non_evidentiary": True,
            "gnn_prediction_is_not_graph_fact": True,
        },
        "boundaries": {
            "core_trains_kg_representation_model": False,
            "core_executes_kg_triple_scoring": False,
            "core_generates_negative_samples": False,
            "core_mutates_evidence_graph_from_kg_score": False,
            "core_promotes_scored_triple_to_evidence_edge": False,
            "core_interprets_low_score_as_falsehood": False,
            "runtime_may_mutate_evidence_graph": False,
            "runtime_may_promote_scored_triple": False,
            "v375_validates_candidate_relationship": False,
        },
        "capabilities": {
            "entity_representation_objects": True,
            "relation_representation_objects": True,
            "knowledge_graph_scoring_function_contracts": True,
            "negative_sampling_provenance": True,
            "triple_scoring_provenance": True,
            "filtered_ranking_evaluation_provenance": True,
            "training_checkpoint_lineage": True,
            "graph_snapshot_binding": True,
        },
        "roadmap_integration": {
            "extends_v370_graph_ml_foundation": True,
            "extends_v371_graph_embedding_runtime": True,
            "extends_v372_node_edge_classification": True,
            "extends_v373_link_prediction_candidates": True,
            "extends_v374_graph_anomaly_detection": True,
            "prepares_v3760_evidence_graph_neural_analysis_validation_workflow": True,
        },
        "reference": {
            "tasks": len(b.tasks),
            "representation_spaces": len(b.representation_spaces),
            "vectors": len(b.vectors),
            "triple_scores": len(b.triple_scores),
            "evaluations": len(b.evaluations),
            "bundle_fingerprint_sha256": b.fingerprint(),
        },
    }
