from __future__ import annotations

import math
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .graph_machine_learning import GraphMLTaskKind, GraphTargetKind
from .graph_classification import GraphClassificationBundle, reference_graph_classification_bundle
from .machine_learning_models import ExecutionHost

CORE_RELEASE = "3.73.0"
CONTRACT_VERSION = "sc.core.graph-link-prediction-candidate-relationship.v1"


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


class LinkPredictionReviewState(str, Enum):
    predicted = "predicted"
    under_review = "under-review"
    human_reviewed = "human-reviewed"
    rejected = "rejected"
    disputed = "disputed"


class CandidateRelationshipState(str, Enum):
    candidate = "candidate"
    under_review = "under-review"
    supported_for_validation = "supported-for-validation"
    rejected = "rejected"
    disputed = "disputed"


class CandidateValidationState(str, Enum):
    unvalidated = "unvalidated"
    evidence_review_required = "evidence-review-required"
    eligible_for_evidence_validation = "eligible-for-evidence-validation"
    rejected = "rejected"
    disputed = "disputed"


class LinkPredictionCalibrationState(str, Enum):
    uncalibrated = "uncalibrated"
    calibrated = "calibrated"
    calibration_unknown = "calibration-unknown"


class LinkPredictionCandidatePair(BaseModel):
    candidate_pair_id: str = Field(min_length=2, max_length=500)
    snapshot_ref: str = Field(min_length=2, max_length=500)
    source_node_ref: str = Field(min_length=2, max_length=1000)
    target_node_ref: str = Field(min_length=2, max_length=1000)
    candidate_generation_method: str = Field(min_length=1, max_length=300)
    candidate_generation_run_ref: str | None = Field(default=None, max_length=1000)
    feature_binding_refs: list[str] = Field(default_factory=list)
    embedding_refs: list[str] = Field(default_factory=list)
    excluded_existing_evidence_edge_refs: list[str] = Field(default_factory=list)
    candidate_pair_is_not_relationship: Literal[True] = True
    candidate_pair_is_not_evidence: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_pair(self):
        if self.source_node_ref == self.target_node_ref:
            raise ValueError("link-prediction candidate pair cannot be self-referential")
        for vals, label in (
            (self.feature_binding_refs, "feature_binding_refs"),
            (self.embedding_refs, "embedding_refs"),
            (self.excluded_existing_evidence_edge_refs, "excluded_existing_evidence_edge_refs"),
        ):
            _unique(vals, label)
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class LinkPredictionTask(BaseModel):
    link_prediction_task_id: str = Field(min_length=2, max_length=500)
    graph_ml_task_kind: Literal[GraphMLTaskKind.link_prediction] = GraphMLTaskKind.link_prediction
    snapshot_ref: str = Field(min_length=2, max_length=500)
    graph_ml_model_foundation_ref: str = Field(min_length=2, max_length=500)
    candidate_pair_refs: list[str] = Field(min_length=1)
    allowed_relationship_types: list[str] = Field(min_length=1)
    no_relationship_label: str = Field(default="no-relationship", min_length=1, max_length=300)
    directed: bool = True
    feature_binding_refs: list[str] = Field(default_factory=list)
    embedding_space_refs: list[str] = Field(default_factory=list)
    leakage_control_refs: list[str] = Field(default_factory=list)
    task_definition_is_not_evidence: Literal[True] = True
    task_does_not_create_missing_edges: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_task(self):
        _unique(self.candidate_pair_refs, "candidate_pair_refs")
        _unique(self.allowed_relationship_types, "allowed_relationship_types")
        if self.no_relationship_label in self.allowed_relationship_types:
            raise ValueError("no_relationship_label must remain distinct from relationship types")
        for vals, label in (
            (self.feature_binding_refs, "feature_binding_refs"),
            (self.embedding_space_refs, "embedding_space_refs"),
            (self.leakage_control_refs, "leakage_control_refs"),
        ):
            _unique(vals, label)
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class LinkPredictionRuntimeContract(BaseModel):
    link_prediction_runtime_contract_id: str = Field(min_length=2, max_length=500)
    extends_graph_ml_runtime_ref: str = Field(min_length=2, max_length=500)
    execution_host: ExecutionHost
    framework: str = Field(min_length=1, max_length=240)
    framework_version: str | None = Field(default=None, max_length=120)
    supports_candidate_generation: bool = True
    supports_relationship_type_scoring: bool = True
    supports_calibration_metadata: bool = True
    core_executes_link_prediction: Literal[False] = False
    runtime_may_mutate_evidence_graph: Literal[False] = False
    runtime_may_promote_candidate_to_evidence_edge: Literal[False] = False
    arbitrary_code_allowed_by_core: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class LinkPredictionModelBinding(BaseModel):
    link_prediction_model_binding_id: str = Field(min_length=2, max_length=500)
    graph_ml_model_foundation_ref: str = Field(min_length=2, max_length=500)
    link_prediction_task_refs: list[str] = Field(min_length=1)
    runtime_contract_ref: str = Field(min_length=2, max_length=500)
    training_run_ref: str = Field(min_length=2, max_length=500)
    checkpoint_ref: str | None = Field(default=None, max_length=1000)
    graph_embedding_space_refs: list[str] = Field(default_factory=list)
    evaluation_refs: list[str] = Field(default_factory=list)
    calibration_refs: list[str] = Field(default_factory=list)
    model_binding_is_not_validation: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_binding(self):
        for vals, label in (
            (self.link_prediction_task_refs, "link_prediction_task_refs"),
            (self.graph_embedding_space_refs, "graph_embedding_space_refs"),
            (self.evaluation_refs, "evaluation_refs"),
            (self.calibration_refs, "calibration_refs"),
        ):
            _unique(vals, label)
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RelationshipTypeProbability(BaseModel):
    relationship_type: str = Field(min_length=1, max_length=300)
    probability: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_probability(self):
        if not math.isfinite(self.probability):
            raise ValueError("relationship probability must be finite")
        return self


class LinkPredictionRecord(BaseModel):
    link_prediction_id: str = Field(min_length=2, max_length=500)
    candidate_pair_ref: str = Field(min_length=2, max_length=500)
    snapshot_ref: str = Field(min_length=2, max_length=500)
    link_prediction_task_ref: str = Field(min_length=2, max_length=500)
    model_binding_ref: str = Field(min_length=2, max_length=500)
    inference_run_ref: str = Field(min_length=2, max_length=500)
    foundation_prediction_ref: str | None = Field(default=None, max_length=500)
    relationship_type_probabilities: list[RelationshipTypeProbability] = Field(min_length=2)
    predicted_relationship_type: str = Field(min_length=1, max_length=300)
    no_relationship_probability: float = Field(ge=0.0, le=1.0)
    score: float | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    calibration_state: LinkPredictionCalibrationState = LinkPredictionCalibrationState.calibration_unknown
    calibration_ref: str | None = Field(default=None, max_length=1000)
    feature_binding_refs: list[str] = Field(default_factory=list)
    embedding_refs: list[str] = Field(default_factory=list)
    explanation_refs: list[str] = Field(default_factory=list)
    review_state: LinkPredictionReviewState = LinkPredictionReviewState.predicted
    reviewer_ref: str | None = Field(default=None, max_length=1000)
    is_graph_fact: Literal[False] = False
    is_evidence: Literal[False] = False
    is_evidence_edge: Literal[False] = False
    high_probability_does_not_establish_relationship: Literal[True] = True
    requires_candidate_relationship_review: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_prediction(self):
        types = [x.relationship_type for x in self.relationship_type_probabilities]
        _unique(types, "relationship_type_probabilities")
        if self.predicted_relationship_type not in types:
            raise ValueError("predicted relationship type must appear in relationship_type_probabilities")
        total = sum(x.probability for x in self.relationship_type_probabilities) + self.no_relationship_probability
        if not math.isclose(total, 1.0, rel_tol=1e-6, abs_tol=1e-6):
            raise ValueError("relationship type probabilities plus no-relationship probability must sum to 1")
        max_rel = max(self.relationship_type_probabilities, key=lambda x: x.probability)
        if max_rel.relationship_type != self.predicted_relationship_type:
            raise ValueError("predicted relationship type must be the maximum-probability relationship type")
        if self.calibration_state == LinkPredictionCalibrationState.calibrated and not self.calibration_ref:
            raise ValueError("calibrated link prediction requires calibration_ref")
        if self.review_state != LinkPredictionReviewState.predicted and not self.reviewer_ref:
            raise ValueError("reviewed link prediction requires reviewer_ref")
        for vals, label in (
            (self.feature_binding_refs, "feature_binding_refs"),
            (self.embedding_refs, "embedding_refs"),
            (self.explanation_refs, "explanation_refs"),
        ):
            _unique(vals, label)
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CandidateRelationship(BaseModel):
    candidate_relationship_id: str = Field(min_length=2, max_length=500)
    link_prediction_ref: str = Field(min_length=2, max_length=500)
    snapshot_ref: str = Field(min_length=2, max_length=500)
    source_node_ref: str = Field(min_length=2, max_length=1000)
    target_node_ref: str = Field(min_length=2, max_length=1000)
    relationship_type_candidate: str = Field(min_length=1, max_length=300)
    supporting_evidence_refs: list[str] = Field(default_factory=list)
    contradicting_evidence_refs: list[str] = Field(default_factory=list)
    contextual_source_refs: list[str] = Field(default_factory=list)
    state: CandidateRelationshipState = CandidateRelationshipState.candidate
    validation_state: CandidateValidationState = CandidateValidationState.unvalidated
    review_record_refs: list[str] = Field(default_factory=list)
    is_graph_fact: Literal[False] = False
    is_evidence: Literal[False] = False
    is_evidence_edge: Literal[False] = False
    candidate_relationship_is_not_validated_relationship: Literal[True] = True
    separate_evidence_validation_required_for_promotion: Literal[True] = True
    model_score_cannot_satisfy_evidence_validation: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_candidate(self):
        if self.source_node_ref == self.target_node_ref:
            raise ValueError("candidate relationship cannot be self-referential")
        for vals, label in (
            (self.supporting_evidence_refs, "supporting_evidence_refs"),
            (self.contradicting_evidence_refs, "contradicting_evidence_refs"),
            (self.contextual_source_refs, "contextual_source_refs"),
            (self.review_record_refs, "review_record_refs"),
        ):
            _unique(vals, label)
        if self.validation_state == CandidateValidationState.eligible_for_evidence_validation and self.state != CandidateRelationshipState.supported_for_validation:
            raise ValueError("eligible-for-evidence-validation candidate must be supported-for-validation")
        if self.state == CandidateRelationshipState.rejected and self.validation_state != CandidateValidationState.rejected:
            raise ValueError("rejected candidate must carry rejected validation state")
        if self.state == CandidateRelationshipState.disputed and self.validation_state != CandidateValidationState.disputed:
            raise ValueError("disputed candidate must carry disputed validation state")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CandidateRelationshipReviewRecord(BaseModel):
    candidate_review_id: str = Field(min_length=2, max_length=500)
    candidate_relationship_ref: str = Field(min_length=2, max_length=500)
    reviewer_ref: str = Field(min_length=2, max_length=1000)
    disposition: CandidateRelationshipState
    validation_state_after_review: CandidateValidationState
    supporting_evidence_refs: list[str] = Field(default_factory=list)
    contradicting_evidence_refs: list[str] = Field(default_factory=list)
    rationale: str | None = Field(default=None, max_length=5000)
    reviewed_at: str | None = Field(default=None, max_length=80)
    review_is_not_truth_determination: Literal[True] = True
    review_does_not_create_evidence_edge: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_review(self):
        if self.disposition == CandidateRelationshipState.candidate:
            raise ValueError("review disposition cannot remain candidate")
        if self.disposition == CandidateRelationshipState.supported_for_validation and self.validation_state_after_review != CandidateValidationState.eligible_for_evidence_validation:
            raise ValueError("supported-for-validation review must set eligible-for-evidence-validation")
        if self.disposition == CandidateRelationshipState.rejected and self.validation_state_after_review != CandidateValidationState.rejected:
            raise ValueError("rejected review must set rejected validation state")
        if self.disposition == CandidateRelationshipState.disputed and self.validation_state_after_review != CandidateValidationState.disputed:
            raise ValueError("disputed review must set disputed validation state")
        _unique(self.supporting_evidence_refs, "review supporting_evidence_refs")
        _unique(self.contradicting_evidence_refs, "review contradicting_evidence_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CandidateRelationshipPromotionGate(BaseModel):
    promotion_gate_id: str = Field(min_length=2, max_length=500)
    candidate_relationship_ref: str = Field(min_length=2, max_length=500)
    human_review_required: Literal[True] = True
    evidence_provenance_required: Literal[True] = True
    contradictory_evidence_review_required: Literal[True] = True
    independent_validation_required: Literal[True] = True
    evidence_edge_creation_occurs_outside_v373: Literal[True] = True
    model_probability_can_satisfy_gate: Literal[False] = False
    embedding_similarity_can_satisfy_gate: Literal[False] = False
    classification_output_can_satisfy_gate: Literal[False] = False
    v373_may_create_evidence_edge: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class LinkPredictionEvaluationRecord(BaseModel):
    link_prediction_evaluation_id: str = Field(min_length=2, max_length=500)
    task_ref: str = Field(min_length=2, max_length=500)
    model_binding_ref: str = Field(min_length=2, max_length=500)
    evaluation_run_ref: str = Field(min_length=2, max_length=500)
    dataset_partition_ref: str = Field(min_length=2, max_length=1000)
    metric_values: dict[str, float] = Field(min_length=1)
    ranking_artifact_ref: str | None = Field(default=None, max_length=1000)
    calibration_artifact_ref: str | None = Field(default=None, max_length=1000)
    metrics_are_descriptive_not_evidence: Literal[True] = True
    evaluation_does_not_establish_relationship_truth: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_eval(self):
        for k, v in self.metric_values.items():
            if not k or not math.isfinite(v):
                raise ValueError("link prediction evaluation metrics require nonempty names and finite values")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class GraphLinkPredictionBundle(BaseModel):
    graph_classification_bundle: GraphClassificationBundle
    candidate_pairs: list[LinkPredictionCandidatePair] = Field(min_length=1)
    tasks: list[LinkPredictionTask] = Field(min_length=1)
    runtime_contracts: list[LinkPredictionRuntimeContract] = Field(min_length=1)
    model_bindings: list[LinkPredictionModelBinding] = Field(min_length=1)
    predictions: list[LinkPredictionRecord] = Field(min_length=1)
    candidate_relationships: list[CandidateRelationship] = Field(min_length=1)
    review_records: list[CandidateRelationshipReviewRecord] = Field(default_factory=list)
    promotion_gates: list[CandidateRelationshipPromotionGate] = Field(min_length=1)
    evaluations: list[LinkPredictionEvaluationRecord] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_bundle(self):
        groups = (
            (self.candidate_pairs, "candidate pairs", "candidate_pair_id"),
            (self.tasks, "tasks", "link_prediction_task_id"),
            (self.runtime_contracts, "runtime contracts", "link_prediction_runtime_contract_id"),
            (self.model_bindings, "model bindings", "link_prediction_model_binding_id"),
            (self.predictions, "predictions", "link_prediction_id"),
            (self.candidate_relationships, "candidate relationships", "candidate_relationship_id"),
            (self.review_records, "review records", "candidate_review_id"),
            (self.promotion_gates, "promotion gates", "promotion_gate_id"),
            (self.evaluations, "evaluations", "link_prediction_evaluation_id"),
        )
        for xs, label, attr in groups:
            _unique([getattr(x, attr) for x in xs], label)

        graph = self.graph_classification_bundle.graph_embedding_bundle.graph_ml_foundation_bundle
        snapshots = {x.snapshot_id: x for x in graph.snapshots}
        foundation_predictions = {x.prediction_id: x for x in graph.predicted_relationships}
        feature_ids = {x.feature_binding_id for x in graph.feature_bindings}
        run_ids = {x.run_id for x in graph.run_provenance}
        runtime_ids = {x.runtime_contract_id for x in graph.runtime_contracts}
        model_ids = {x.foundation_id for x in graph.model_foundations}
        embedding_bundle = self.graph_classification_bundle.graph_embedding_bundle
        embedding_ids = {x.embedding_id for x in embedding_bundle.embeddings}
        embedding_space_ids = {x.embedding_space_id for x in embedding_bundle.embedding_spaces}

        pairs = {x.candidate_pair_id: x for x in self.candidate_pairs}
        tasks = {x.link_prediction_task_id: x for x in self.tasks}
        runtimes = {x.link_prediction_runtime_contract_id: x for x in self.runtime_contracts}
        bindings = {x.link_prediction_model_binding_id: x for x in self.model_bindings}
        predictions = {x.link_prediction_id: x for x in self.predictions}
        candidates = {x.candidate_relationship_id: x for x in self.candidate_relationships}
        reviews = {x.candidate_review_id: x for x in self.review_records}

        for pair in self.candidate_pairs:
            if pair.snapshot_ref not in snapshots:
                raise ValueError("candidate pair snapshot must resolve")
            snap = snapshots[pair.snapshot_ref]
            if pair.source_node_ref not in snap.node_refs or pair.target_node_ref not in snap.node_refs:
                raise ValueError("candidate pair endpoints must resolve to snapshot nodes")
            if any(x not in feature_ids for x in pair.feature_binding_refs):
                raise ValueError("candidate pair feature refs must resolve")
            if any(x not in embedding_ids for x in pair.embedding_refs):
                raise ValueError("candidate pair embedding refs must resolve")
            evidence_edge_refs = {x.evidence_edge_ref for x in snap.evidence_edges}
            if any(x not in evidence_edge_refs for x in pair.excluded_existing_evidence_edge_refs):
                raise ValueError("excluded existing evidence edge refs must resolve")

        for task in self.tasks:
            if task.snapshot_ref not in snapshots or task.graph_ml_model_foundation_ref not in model_ids:
                raise ValueError("link prediction task graph references must resolve")
            if any(x not in pairs for x in task.candidate_pair_refs):
                raise ValueError("link prediction task candidate pairs must resolve")
            if any(x not in feature_ids for x in task.feature_binding_refs):
                raise ValueError("link prediction task feature refs must resolve")
            if any(x not in embedding_space_ids for x in task.embedding_space_refs):
                raise ValueError("link prediction task embedding spaces must resolve")

        for runtime in self.runtime_contracts:
            if runtime.extends_graph_ml_runtime_ref not in runtime_ids:
                raise ValueError("link prediction runtime must extend a known graph ML runtime")

        for binding in self.model_bindings:
            if binding.graph_ml_model_foundation_ref not in model_ids or binding.runtime_contract_ref not in runtimes:
                raise ValueError("link prediction model binding references must resolve")
            if any(x not in tasks for x in binding.link_prediction_task_refs):
                raise ValueError("link prediction model binding tasks must resolve")
            if binding.training_run_ref not in run_ids:
                raise ValueError("link prediction training run must resolve")
            if any(x not in embedding_space_ids for x in binding.graph_embedding_space_refs):
                raise ValueError("link prediction model binding embedding spaces must resolve")

        for prediction in self.predictions:
            if prediction.candidate_pair_ref not in pairs or prediction.link_prediction_task_ref not in tasks or prediction.model_binding_ref not in bindings:
                raise ValueError("link prediction references must resolve")
            pair = pairs[prediction.candidate_pair_ref]
            task = tasks[prediction.link_prediction_task_ref]
            if prediction.snapshot_ref != pair.snapshot_ref or prediction.snapshot_ref != task.snapshot_ref:
                raise ValueError("link prediction snapshot must match pair and task")
            if prediction.predicted_relationship_type not in task.allowed_relationship_types:
                raise ValueError("predicted relationship type must be allowed by task")
            if any(x.relationship_type not in task.allowed_relationship_types for x in prediction.relationship_type_probabilities):
                raise ValueError("relationship type probabilities must use task relationship types")
            if prediction.inference_run_ref not in run_ids:
                raise ValueError("link prediction inference run must resolve")
            if prediction.foundation_prediction_ref and prediction.foundation_prediction_ref not in foundation_predictions:
                raise ValueError("foundation prediction ref must resolve")
            if any(x not in feature_ids for x in prediction.feature_binding_refs):
                raise ValueError("link prediction feature refs must resolve")
            if any(x not in embedding_ids for x in prediction.embedding_refs):
                raise ValueError("link prediction embedding refs must resolve")

        for candidate in self.candidate_relationships:
            if candidate.link_prediction_ref not in predictions or candidate.snapshot_ref not in snapshots:
                raise ValueError("candidate relationship references must resolve")
            prediction = predictions[candidate.link_prediction_ref]
            pair = pairs[prediction.candidate_pair_ref]
            if candidate.source_node_ref != pair.source_node_ref or candidate.target_node_ref != pair.target_node_ref:
                raise ValueError("candidate relationship endpoints must match prediction pair")
            if candidate.relationship_type_candidate != prediction.predicted_relationship_type:
                raise ValueError("candidate relationship type must match prediction")
            snap = snapshots[candidate.snapshot_ref]
            if any(e.source_node_ref == candidate.source_node_ref and e.target_node_ref == candidate.target_node_ref and e.relationship_type == candidate.relationship_type_candidate for e in snap.evidence_edges):
                raise ValueError("candidate relationship cannot duplicate an existing evidence edge")
            if any(x not in reviews for x in candidate.review_record_refs):
                raise ValueError("candidate relationship review refs must resolve")

        for review in self.review_records:
            if review.candidate_relationship_ref not in candidates:
                raise ValueError("candidate review must resolve to candidate relationship")

        for gate in self.promotion_gates:
            if gate.candidate_relationship_ref not in candidates:
                raise ValueError("promotion gate must resolve to candidate relationship")

        for evaluation in self.evaluations:
            if evaluation.task_ref not in tasks or evaluation.model_binding_ref not in bindings:
                raise ValueError("link prediction evaluation refs must resolve")

        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


def reference_graph_link_prediction_bundle() -> GraphLinkPredictionBundle:
    cb = reference_graph_classification_bundle()
    graph = cb.graph_embedding_bundle.graph_ml_foundation_bundle
    eb = cb.graph_embedding_bundle
    snapshot = graph.snapshots[0]
    base_prediction = graph.predicted_relationships[0]
    source = base_prediction.source_node_ref
    target = base_prediction.target_node_ref

    pair = LinkPredictionCandidatePair(
        candidate_pair_id="graph-link-pair:reference:en-es:v1",
        snapshot_ref=snapshot.snapshot_id,
        source_node_ref=source,
        target_node_ref=target,
        candidate_generation_method="graph-embedding-nearest-neighbor",
        candidate_generation_run_ref=graph.run_provenance[1].run_id,
        feature_binding_refs=[graph.feature_bindings[0].feature_binding_id],
        embedding_refs=[eb.embeddings[0].embedding_id, eb.embeddings[2].embedding_id],
        metadata={"synthetic_reference": True},
    )
    task = LinkPredictionTask(
        link_prediction_task_id="graph-link-task:reference:v1",
        snapshot_ref=snapshot.snapshot_id,
        graph_ml_model_foundation_ref=graph.model_foundations[0].foundation_id,
        candidate_pair_refs=[pair.candidate_pair_id],
        allowed_relationship_types=["semantic-related", "translation-related"],
        feature_binding_refs=[graph.feature_bindings[0].feature_binding_id],
        embedding_space_refs=[eb.embedding_spaces[0].embedding_space_id],
        leakage_control_refs=["leakage-control:reference:no-target-edge:v1"],
    )
    runtime = LinkPredictionRuntimeContract(
        link_prediction_runtime_contract_id="graph-link-runtime:reference:v1",
        extends_graph_ml_runtime_ref=graph.runtime_contracts[0].runtime_contract_id,
        execution_host=ExecutionHost.workspace,
        framework="pytorch-geometric",
        framework_version="reference",
    )
    binding = LinkPredictionModelBinding(
        link_prediction_model_binding_id="graph-link-model-binding:reference:v1",
        graph_ml_model_foundation_ref=graph.model_foundations[0].foundation_id,
        link_prediction_task_refs=[task.link_prediction_task_id],
        runtime_contract_ref=runtime.link_prediction_runtime_contract_id,
        training_run_ref=graph.run_provenance[0].run_id,
        graph_embedding_space_refs=[eb.embedding_spaces[0].embedding_space_id],
        evaluation_refs=["graph-link-evaluation:reference:v1"],
        calibration_refs=["calibration:reference:link-temperature:v1"],
    )
    prediction = LinkPredictionRecord(
        link_prediction_id="graph-link-prediction:reference:en-es:v1",
        candidate_pair_ref=pair.candidate_pair_id,
        snapshot_ref=snapshot.snapshot_id,
        link_prediction_task_ref=task.link_prediction_task_id,
        model_binding_ref=binding.link_prediction_model_binding_id,
        inference_run_ref=graph.run_provenance[1].run_id,
        foundation_prediction_ref=base_prediction.prediction_id,
        relationship_type_probabilities=[
            RelationshipTypeProbability(relationship_type="semantic-related", probability=0.72),
            RelationshipTypeProbability(relationship_type="translation-related", probability=0.15),
        ],
        predicted_relationship_type="semantic-related",
        no_relationship_probability=0.13,
        score=2.31,
        confidence=0.87,
        calibration_state=LinkPredictionCalibrationState.calibrated,
        calibration_ref="calibration:reference:link-temperature:v1",
        feature_binding_refs=[graph.feature_bindings[0].feature_binding_id],
        embedding_refs=[eb.embeddings[0].embedding_id, eb.embeddings[2].embedding_id],
        explanation_refs=["explanation:reference:graph-link:v1"],
    )
    review = CandidateRelationshipReviewRecord(
        candidate_review_id="candidate-review:reference:en-es:v1",
        candidate_relationship_ref="candidate-relationship:reference:en-es:v1",
        reviewer_ref="reviewer:reference:human:v1",
        disposition=CandidateRelationshipState.supported_for_validation,
        validation_state_after_review=CandidateValidationState.eligible_for_evidence_validation,
        supporting_evidence_refs=["alignment:es-a:water"],
        rationale="Synthetic reference review: candidate may proceed to a separate evidence-validation workflow; it is not an evidence edge.",
        reviewed_at="2026-09-29T00:00:00Z",
    )
    candidate = CandidateRelationship(
        candidate_relationship_id="candidate-relationship:reference:en-es:v1",
        link_prediction_ref=prediction.link_prediction_id,
        snapshot_ref=snapshot.snapshot_id,
        source_node_ref=source,
        target_node_ref=target,
        relationship_type_candidate="semantic-related",
        supporting_evidence_refs=["alignment:es-a:water"],
        contextual_source_refs=["cross-lingual-exchange:reference"],
        state=CandidateRelationshipState.supported_for_validation,
        validation_state=CandidateValidationState.eligible_for_evidence_validation,
        review_record_refs=[review.candidate_review_id],
        metadata={"synthetic_reference": True, "not_promoted": True},
    )
    gate = CandidateRelationshipPromotionGate(
        promotion_gate_id="candidate-promotion-gate:reference:en-es:v1",
        candidate_relationship_ref=candidate.candidate_relationship_id,
    )
    evaluation = LinkPredictionEvaluationRecord(
        link_prediction_evaluation_id="graph-link-evaluation:reference:v1",
        task_ref=task.link_prediction_task_id,
        model_binding_ref=binding.link_prediction_model_binding_id,
        evaluation_run_ref="graph-link-eval-run:reference:v1",
        dataset_partition_ref="dataset-partition:reference:test",
        metric_values={"auroc": 0.90, "average_precision": 0.86, "hits_at_10": 0.80},
        calibration_artifact_ref="calibration:reference:link-temperature:v1",
    )
    return GraphLinkPredictionBundle(
        graph_classification_bundle=cb,
        candidate_pairs=[pair],
        tasks=[task],
        runtime_contracts=[runtime],
        model_bindings=[binding],
        predictions=[prediction],
        candidate_relationships=[candidate],
        review_records=[review],
        promotion_gates=[gate],
        evaluations=[evaluation],
        metadata={
            "reference_fixture": "synthetic-contract-fixture",
            "gnn_prediction_is_not_graph_fact": True,
            "candidate_relationship_is_not_evidence_edge": True,
            "v373_does_not_promote_candidates": True,
        },
    )


def contract_document() -> dict[str, Any]:
    b = reference_graph_link_prediction_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "extends_contracts": [
            "sc.core.graph-machine-learning-foundation.v1",
            "sc.core.graph-embedding-runtime.v1",
            "sc.core.graph-node-edge-classification.v1",
        ],
        "object_types": [
            "LinkPredictionCandidatePair",
            "LinkPredictionTask",
            "LinkPredictionRuntimeContract",
            "LinkPredictionModelBinding",
            "RelationshipTypeProbability",
            "LinkPredictionRecord",
            "CandidateRelationship",
            "CandidateRelationshipReviewRecord",
            "CandidateRelationshipPromotionGate",
            "LinkPredictionEvaluationRecord",
            "GraphLinkPredictionBundle",
        ],
        "principles": {
            "link_prediction_is_derived_model_output": True,
            "predicted_link_is_not_graph_fact": True,
            "predicted_link_is_not_evidence": True,
            "candidate_relationship_is_not_graph_fact": True,
            "candidate_relationship_is_not_evidence_edge": True,
            "human_review_does_not_create_evidence_edge": True,
            "high_probability_does_not_establish_relationship": True,
            "embedding_similarity_does_not_establish_relationship": True,
            "classification_output_does_not_establish_relationship": True,
            "contradicting_evidence_must_remain_visible": True,
            "gnn_prediction_is_not_graph_fact": True,
        },
        "boundaries": {
            "core_generates_candidate_pairs": False,
            "core_trains_link_predictor": False,
            "core_runs_link_prediction_inference": False,
            "core_promotes_candidate_to_evidence_edge": False,
            "core_mutates_evidence_graph_from_link_prediction": False,
            "runtime_may_mutate_evidence_graph": False,
            "runtime_may_promote_candidate_to_evidence_edge": False,
            "v373_creates_evidence_edges_from_predictions": False,
            "v373_determines_relationship_truth": False,
        },
        "promotion_requirements": {
            "human_review_required": True,
            "evidence_provenance_required": True,
            "contradictory_evidence_review_required": True,
            "independent_validation_required": True,
            "actual_evidence_edge_creation_occurs_outside_v373": True,
        },
        "roadmap_integration": {
            "extends_v370_graph_ml_foundation": True,
            "extends_v371_graph_embedding_runtime": True,
            "extends_v372_node_edge_classification": True,
            "prepares_v3740_graph_anomaly_detection": True,
            "prepares_v3750_knowledge_graph_representation_learning": True,
            "prepares_v3760_evidence_graph_neural_analysis_validation_workflow": True,
        },
        "reference": {
            "candidate_pairs": len(b.candidate_pairs),
            "predictions": len(b.predictions),
            "candidate_relationships": len(b.candidate_relationships),
            "review_records": len(b.review_records),
            "promotion_gates": len(b.promotion_gates),
            "evaluations": len(b.evaluations),
            "bundle_fingerprint_sha256": b.fingerprint(),
        },
    }
