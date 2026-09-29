from __future__ import annotations

import math
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .graph_machine_learning import GraphMLTaskKind
from .graph_link_prediction import GraphLinkPredictionBundle, reference_graph_link_prediction_bundle
from .machine_learning_models import ExecutionHost

CORE_RELEASE = "3.74.0"
CONTRACT_VERSION = "sc.core.graph-anomaly-detection.v1"


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


class GraphAnomalyTargetKind(str, Enum):
    node = "node"
    edge = "edge"
    subgraph = "subgraph"
    graph = "graph"


class GraphAnomalyKind(str, Enum):
    structural = "structural"
    feature = "feature"
    embedding = "embedding"
    temporal = "temporal"
    relational = "relational"
    hybrid = "hybrid"


class GraphAnomalyReviewState(str, Enum):
    detected = "detected"
    under_review = "under-review"
    human_reviewed = "human-reviewed"
    rejected = "rejected"
    disputed = "disputed"


class GraphAnomalyDisposition(str, Enum):
    retain_for_investigation = "retain-for-investigation"
    benign_variation = "benign-variation"
    data_quality_issue = "data-quality-issue"
    model_artifact = "model-artifact"
    rejected = "rejected"
    disputed = "disputed"


class GraphAnomalyCalibrationState(str, Enum):
    uncalibrated = "uncalibrated"
    calibrated = "calibrated"
    calibration_unknown = "calibration-unknown"


class GraphAnomalyDetectionTask(BaseModel):
    anomaly_task_id: str = Field(min_length=2, max_length=500)
    graph_ml_task_kind: Literal[GraphMLTaskKind.anomaly_detection] = GraphMLTaskKind.anomaly_detection
    snapshot_ref: str = Field(min_length=2, max_length=500)
    target_kinds: list[GraphAnomalyTargetKind] = Field(min_length=1)
    anomaly_kinds: list[GraphAnomalyKind] = Field(min_length=1)
    detector_model_ref: str = Field(min_length=2, max_length=500)
    feature_binding_refs: list[str] = Field(default_factory=list)
    embedding_space_refs: list[str] = Field(default_factory=list)
    temporal_context_refs: list[str] = Field(default_factory=list)
    threshold_policy_ref: str = Field(min_length=2, max_length=1000)
    task_definition_is_not_evidence: Literal[True] = True
    task_does_not_label_wrongdoing: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_task(self):
        _unique([x.value for x in self.target_kinds], "target_kinds")
        _unique([x.value for x in self.anomaly_kinds], "anomaly_kinds")
        for xs, label in ((self.feature_binding_refs,"feature_binding_refs"),(self.embedding_space_refs,"embedding_space_refs"),(self.temporal_context_refs,"temporal_context_refs")):
            _unique(xs,label)
        return self

    def fingerprint(self) -> str: return canonical_sha256(self)


class GraphAnomalyRuntimeContract(BaseModel):
    anomaly_runtime_contract_id: str = Field(min_length=2, max_length=500)
    extends_graph_ml_runtime_ref: str = Field(min_length=2, max_length=500)
    execution_host: ExecutionHost
    framework: str = Field(min_length=1, max_length=240)
    framework_version: str | None = Field(default=None, max_length=120)
    supported_anomaly_kinds: list[GraphAnomalyKind] = Field(min_length=1)
    supports_score_calibration: bool = True
    supports_explanation_artifacts: bool = True
    core_executes_anomaly_detection: Literal[False] = False
    runtime_may_mutate_evidence_graph: Literal[False] = False
    runtime_may_assert_wrongdoing: Literal[False] = False
    arbitrary_code_allowed_by_core: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_runtime(self):
        _unique([x.value for x in self.supported_anomaly_kinds], "supported_anomaly_kinds")
        return self

    def fingerprint(self) -> str: return canonical_sha256(self)


class GraphAnomalyDetectorBinding(BaseModel):
    detector_binding_id: str = Field(min_length=2, max_length=500)
    detector_model_ref: str = Field(min_length=2, max_length=500)
    graph_ml_model_foundation_ref: str = Field(min_length=2, max_length=500)
    task_refs: list[str] = Field(min_length=1)
    runtime_contract_ref: str = Field(min_length=2, max_length=500)
    training_run_ref: str | None = Field(default=None, max_length=500)
    checkpoint_ref: str | None = Field(default=None, max_length=1000)
    embedding_space_refs: list[str] = Field(default_factory=list)
    calibration_refs: list[str] = Field(default_factory=list)
    evaluation_refs: list[str] = Field(default_factory=list)
    detector_binding_is_not_validation: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_binding(self):
        for xs,label in ((self.task_refs,"task_refs"),(self.embedding_space_refs,"embedding_space_refs"),(self.calibration_refs,"calibration_refs"),(self.evaluation_refs,"evaluation_refs")):
            _unique(xs,label)
        return self

    def fingerprint(self) -> str: return canonical_sha256(self)


class GraphAnomalyTarget(BaseModel):
    anomaly_target_id: str = Field(min_length=2, max_length=500)
    snapshot_ref: str = Field(min_length=2, max_length=500)
    target_kind: GraphAnomalyTargetKind
    object_ref: str | None = Field(default=None, max_length=1000)
    member_node_refs: list[str] = Field(default_factory=list)
    member_edge_refs: list[str] = Field(default_factory=list)
    observation_window_start: str | None = Field(default=None, max_length=80)
    observation_window_end: str | None = Field(default=None, max_length=80)
    target_definition_is_not_anomaly_finding: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_target(self):
        _unique(self.member_node_refs,"member_node_refs"); _unique(self.member_edge_refs,"member_edge_refs")
        if self.target_kind in (GraphAnomalyTargetKind.node, GraphAnomalyTargetKind.edge) and not self.object_ref:
            raise ValueError("node/edge anomaly target requires object_ref")
        if self.target_kind == GraphAnomalyTargetKind.subgraph and not (self.member_node_refs or self.member_edge_refs):
            raise ValueError("subgraph anomaly target requires members")
        if self.target_kind == GraphAnomalyTargetKind.graph and self.object_ref is not None:
            raise ValueError("graph anomaly target represents the snapshot and must not set object_ref")
        return self

    def fingerprint(self) -> str: return canonical_sha256(self)


class GraphAnomalyScoreRecord(BaseModel):
    anomaly_score_id: str = Field(min_length=2, max_length=500)
    anomaly_target_ref: str = Field(min_length=2, max_length=500)
    anomaly_task_ref: str = Field(min_length=2, max_length=500)
    detector_binding_ref: str = Field(min_length=2, max_length=500)
    inference_run_ref: str = Field(min_length=2, max_length=500)
    anomaly_kind: GraphAnomalyKind
    raw_score: float
    normalized_score: float = Field(ge=0.0, le=1.0)
    threshold: float = Field(ge=0.0, le=1.0)
    flagged_as_anomalous: bool
    calibration_state: GraphAnomalyCalibrationState = GraphAnomalyCalibrationState.calibration_unknown
    calibration_ref: str | None = Field(default=None, max_length=1000)
    baseline_ref: str | None = Field(default=None, max_length=1000)
    feature_binding_refs: list[str] = Field(default_factory=list)
    embedding_refs: list[str] = Field(default_factory=list)
    explanation_refs: list[str] = Field(default_factory=list)
    review_state: GraphAnomalyReviewState = GraphAnomalyReviewState.detected
    reviewer_ref: str | None = Field(default=None, max_length=1000)
    is_graph_fact: Literal[False] = False
    is_evidence: Literal[False] = False
    is_wrongdoing_finding: Literal[False] = False
    anomaly_score_is_not_evidence_strength: Literal[True] = True
    anomaly_flag_requires_contextual_review: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_score(self):
        if not math.isfinite(self.raw_score) or not math.isfinite(self.normalized_score) or not math.isfinite(self.threshold):
            raise ValueError("anomaly scores and threshold must be finite")
        if self.flagged_as_anomalous != (self.normalized_score >= self.threshold):
            raise ValueError("anomaly flag must match normalized score threshold rule")
        if self.calibration_state == GraphAnomalyCalibrationState.calibrated and not self.calibration_ref:
            raise ValueError("calibrated anomaly score requires calibration_ref")
        if self.review_state == GraphAnomalyReviewState.human_reviewed and not self.reviewer_ref:
            raise ValueError("human-reviewed anomaly score requires reviewer_ref")
        for xs,label in ((self.feature_binding_refs,"feature_binding_refs"),(self.embedding_refs,"embedding_refs"),(self.explanation_refs,"explanation_refs")):
            _unique(xs,label)
        return self

    def fingerprint(self) -> str: return canonical_sha256(self)


class GraphAnomalyExplanationRecord(BaseModel):
    anomaly_explanation_id: str = Field(min_length=2, max_length=500)
    anomaly_score_ref: str = Field(min_length=2, max_length=500)
    method: str = Field(min_length=1, max_length=300)
    summary: str = Field(min_length=1, max_length=5000)
    contributing_feature_refs: list[str] = Field(default_factory=list)
    contributing_embedding_refs: list[str] = Field(default_factory=list)
    comparison_refs: list[str] = Field(default_factory=list)
    explanation_is_not_causal_proof: Literal[True] = True
    explanation_is_not_evidence: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_explanation(self):
        for xs,label in ((self.contributing_feature_refs,"contributing_feature_refs"),(self.contributing_embedding_refs,"contributing_embedding_refs"),(self.comparison_refs,"comparison_refs")):
            _unique(xs,label)
        return self

    def fingerprint(self) -> str: return canonical_sha256(self)


class GraphAnomalyReviewRecord(BaseModel):
    anomaly_review_id: str = Field(min_length=2, max_length=500)
    anomaly_score_ref: str = Field(min_length=2, max_length=500)
    reviewer_ref: str = Field(min_length=2, max_length=1000)
    disposition: GraphAnomalyDisposition
    supporting_evidence_refs: list[str] = Field(default_factory=list)
    contradicting_evidence_refs: list[str] = Field(default_factory=list)
    contextual_source_refs: list[str] = Field(default_factory=list)
    rationale: str | None = Field(default=None, max_length=5000)
    reviewed_at: str | None = Field(default=None, max_length=80)
    review_is_not_truth_determination: Literal[True] = True
    review_is_not_wrongdoing_determination: Literal[True] = True
    review_does_not_create_evidence_edge: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_review(self):
        for xs,label in ((self.supporting_evidence_refs,"supporting_evidence_refs"),(self.contradicting_evidence_refs,"contradicting_evidence_refs"),(self.contextual_source_refs,"contextual_source_refs")):
            _unique(xs,label)
        return self

    def fingerprint(self) -> str: return canonical_sha256(self)


class GraphAnomalyEvaluationRecord(BaseModel):
    anomaly_evaluation_id: str = Field(min_length=2, max_length=500)
    anomaly_task_ref: str = Field(min_length=2, max_length=500)
    detector_binding_ref: str = Field(min_length=2, max_length=500)
    evaluation_run_ref: str = Field(min_length=2, max_length=500)
    dataset_partition_ref: str = Field(min_length=2, max_length=1000)
    metric_values: dict[str, float] = Field(min_length=1)
    threshold_policy_ref: str = Field(min_length=2, max_length=1000)
    calibration_artifact_ref: str | None = Field(default=None, max_length=1000)
    metrics_are_descriptive_not_evidence: Literal[True] = True
    evaluation_does_not_establish_anomaly_truth: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_eval(self):
        for k,v in self.metric_values.items():
            if not k or not math.isfinite(v): raise ValueError("anomaly evaluation metrics require names and finite values")
        return self

    def fingerprint(self) -> str: return canonical_sha256(self)


class GraphAnomalyDetectionBundle(BaseModel):
    graph_link_prediction_bundle: GraphLinkPredictionBundle
    tasks: list[GraphAnomalyDetectionTask] = Field(min_length=1)
    runtime_contracts: list[GraphAnomalyRuntimeContract] = Field(min_length=1)
    detector_bindings: list[GraphAnomalyDetectorBinding] = Field(min_length=1)
    targets: list[GraphAnomalyTarget] = Field(min_length=1)
    scores: list[GraphAnomalyScoreRecord] = Field(min_length=1)
    explanations: list[GraphAnomalyExplanationRecord] = Field(default_factory=list)
    reviews: list[GraphAnomalyReviewRecord] = Field(default_factory=list)
    evaluations: list[GraphAnomalyEvaluationRecord] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_bundle(self):
        groups=((self.tasks,"tasks","anomaly_task_id"),(self.runtime_contracts,"runtime contracts","anomaly_runtime_contract_id"),(self.detector_bindings,"detector bindings","detector_binding_id"),(self.targets,"targets","anomaly_target_id"),(self.scores,"scores","anomaly_score_id"),(self.explanations,"explanations","anomaly_explanation_id"),(self.reviews,"reviews","anomaly_review_id"),(self.evaluations,"evaluations","anomaly_evaluation_id"))
        for xs,label,attr in groups: _unique([getattr(x,attr) for x in xs],label)
        lp=self.graph_link_prediction_bundle
        gb=lp.graph_classification_bundle.graph_embedding_bundle
        graph=gb.graph_ml_foundation_bundle
        snapshots={x.snapshot_id:x for x in graph.snapshots}
        snapshot=graph.snapshots[0]
        feature_ids={x.feature_binding_id for x in graph.feature_bindings}
        embedding_ids={x.embedding_id for x in gb.embeddings}
        embedding_space_ids={x.embedding_space_id for x in gb.embedding_spaces}
        graph_runtime_ids={x.runtime_contract_id for x in graph.runtime_contracts}
        model_ids={x.foundation_id for x in graph.model_foundations}
        run_ids={x.run_id for x in graph.run_provenance}
        evidence_edges={x.evidence_edge_ref:x for x in snapshot.evidence_edges}
        tasks={x.anomaly_task_id:x for x in self.tasks}; runtimes={x.anomaly_runtime_contract_id:x for x in self.runtime_contracts}; bindings={x.detector_binding_id:x for x in self.detector_bindings}; targets={x.anomaly_target_id:x for x in self.targets}; scores={x.anomaly_score_id:x for x in self.scores}; explanations={x.anomaly_explanation_id:x for x in self.explanations}
        for task in self.tasks:
            if task.snapshot_ref not in snapshots: raise ValueError("anomaly task snapshot must resolve")
            if any(x not in feature_ids for x in task.feature_binding_refs): raise ValueError("anomaly task feature refs must resolve")
            if any(x not in embedding_space_ids for x in task.embedding_space_refs): raise ValueError("anomaly task embedding spaces must resolve")
        for runtime in self.runtime_contracts:
            if runtime.extends_graph_ml_runtime_ref not in graph_runtime_ids: raise ValueError("anomaly runtime must extend graph ML runtime")
        for binding in self.detector_bindings:
            if binding.graph_ml_model_foundation_ref not in model_ids: raise ValueError("detector foundation ref must resolve")
            if binding.runtime_contract_ref not in runtimes: raise ValueError("detector runtime ref must resolve")
            if any(x not in tasks for x in binding.task_refs): raise ValueError("detector task refs must resolve")
            if binding.training_run_ref and binding.training_run_ref not in run_ids: raise ValueError("detector training run must resolve")
            if any(x not in embedding_space_ids for x in binding.embedding_space_refs): raise ValueError("detector embedding spaces must resolve")
        for target in self.targets:
            if target.snapshot_ref not in snapshots: raise ValueError("anomaly target snapshot must resolve")
            snap=snapshots[target.snapshot_ref]
            if target.target_kind==GraphAnomalyTargetKind.node and target.object_ref not in snap.node_refs: raise ValueError("node anomaly target must resolve")
            if target.target_kind==GraphAnomalyTargetKind.edge and target.object_ref not in {x.evidence_edge_ref for x in snap.evidence_edges}: raise ValueError("edge anomaly target must resolve")
            if any(x not in snap.node_refs for x in target.member_node_refs): raise ValueError("subgraph node refs must resolve")
            if any(x not in {e.evidence_edge_ref for e in snap.evidence_edges} for x in target.member_edge_refs): raise ValueError("subgraph edge refs must resolve")
        for score in self.scores:
            if score.anomaly_target_ref not in targets or score.anomaly_task_ref not in tasks or score.detector_binding_ref not in bindings: raise ValueError("anomaly score references must resolve")
            if score.inference_run_ref not in run_ids: raise ValueError("anomaly inference run must resolve")
            if score.anomaly_kind not in tasks[score.anomaly_task_ref].anomaly_kinds: raise ValueError("anomaly score kind must be allowed by task")
            if any(x not in feature_ids for x in score.feature_binding_refs): raise ValueError("anomaly score feature refs must resolve")
            if any(x not in embedding_ids for x in score.embedding_refs): raise ValueError("anomaly score embedding refs must resolve")
            if any(x not in explanations for x in score.explanation_refs): raise ValueError("anomaly explanation refs must resolve")
        for exp in self.explanations:
            if exp.anomaly_score_ref not in scores: raise ValueError("anomaly explanation score ref must resolve")
            if any(x not in feature_ids for x in exp.contributing_feature_refs): raise ValueError("explanation feature refs must resolve")
            if any(x not in embedding_ids for x in exp.contributing_embedding_refs): raise ValueError("explanation embedding refs must resolve")
        for review in self.reviews:
            if review.anomaly_score_ref not in scores: raise ValueError("anomaly review score ref must resolve")
        for evaluation in self.evaluations:
            if evaluation.anomaly_task_ref not in tasks or evaluation.detector_binding_ref not in bindings: raise ValueError("anomaly evaluation refs must resolve")
        return self

    def fingerprint(self) -> str: return canonical_sha256(self)


def reference_graph_anomaly_detection_bundle() -> GraphAnomalyDetectionBundle:
    lp=reference_graph_link_prediction_bundle()
    gb=lp.graph_classification_bundle.graph_embedding_bundle
    graph=gb.graph_ml_foundation_bundle
    snap=graph.snapshots[0]
    feature=graph.feature_bindings[0]
    emb=gb.embeddings[2]
    task=GraphAnomalyDetectionTask(
        anomaly_task_id="graph-anomaly-task:reference:v1", snapshot_ref=snap.snapshot_id,
        target_kinds=[GraphAnomalyTargetKind.node,GraphAnomalyTargetKind.edge,GraphAnomalyTargetKind.subgraph],
        anomaly_kinds=[GraphAnomalyKind.structural,GraphAnomalyKind.embedding,GraphAnomalyKind.hybrid],
        detector_model_ref="graph-anomaly-detector:reference:v1", feature_binding_refs=[feature.feature_binding_id],
        embedding_space_refs=[gb.embedding_spaces[0].embedding_space_id], threshold_policy_ref="threshold-policy:reference:p95:v1",
        metadata={"synthetic_reference":True})
    runtime=GraphAnomalyRuntimeContract(
        anomaly_runtime_contract_id="graph-anomaly-runtime:reference:v1", extends_graph_ml_runtime_ref=graph.runtime_contracts[0].runtime_contract_id,
        execution_host=ExecutionHost.workspace, framework="pytorch-geometric-compatible", framework_version="external",
        supported_anomaly_kinds=[GraphAnomalyKind.structural,GraphAnomalyKind.embedding,GraphAnomalyKind.hybrid])
    binding=GraphAnomalyDetectorBinding(
        detector_binding_id="graph-anomaly-binding:reference:v1", detector_model_ref=task.detector_model_ref,
        graph_ml_model_foundation_ref=graph.model_foundations[0].foundation_id, task_refs=[task.anomaly_task_id],
        runtime_contract_ref=runtime.anomaly_runtime_contract_id, training_run_ref=graph.run_provenance[0].run_id,
        embedding_space_refs=[gb.embedding_spaces[0].embedding_space_id], calibration_refs=["calibration:reference:anomaly:v1"],
        evaluation_refs=["graph-anomaly-evaluation:reference:v1"])
    target=GraphAnomalyTarget(anomaly_target_id="graph-anomaly-target:reference:es-node:v1",snapshot_ref=snap.snapshot_id,target_kind=GraphAnomalyTargetKind.node,object_ref=snap.node_refs[2],metadata={"synthetic_reference":True})
    score=GraphAnomalyScoreRecord(
        anomaly_score_id="graph-anomaly-score:reference:es-node:v1", anomaly_target_ref=target.anomaly_target_id,
        anomaly_task_ref=task.anomaly_task_id, detector_binding_ref=binding.detector_binding_id,
        inference_run_ref=graph.run_provenance[1].run_id, anomaly_kind=GraphAnomalyKind.embedding,
        raw_score=2.41, normalized_score=.91, threshold=.80, flagged_as_anomalous=True,
        calibration_state=GraphAnomalyCalibrationState.calibrated, calibration_ref="calibration:reference:anomaly:v1",
        baseline_ref="baseline:reference:graph-embedding-neighborhood:v1", feature_binding_refs=[feature.feature_binding_id],
        embedding_refs=[emb.embedding_id], explanation_refs=["graph-anomaly-explanation:reference:es-node:v1"],
        metadata={"synthetic_reference":True,"not_wrongdoing":True})
    explanation=GraphAnomalyExplanationRecord(
        anomaly_explanation_id="graph-anomaly-explanation:reference:es-node:v1", anomaly_score_ref=score.anomaly_score_id,
        method="embedding-neighborhood-deviation", summary="Synthetic reference deviation from the comparison neighborhood; not evidence of error, misconduct, or a factual graph defect.",
        contributing_feature_refs=[feature.feature_binding_id], contributing_embedding_refs=[emb.embedding_id],
        comparison_refs=["baseline:reference:graph-embedding-neighborhood:v1"])
    review=GraphAnomalyReviewRecord(
        anomaly_review_id="graph-anomaly-review:reference:es-node:v1", anomaly_score_ref=score.anomaly_score_id,
        reviewer_ref="reviewer:reference:human:v1", disposition=GraphAnomalyDisposition.retain_for_investigation,
        supporting_evidence_refs=["alignment:es-a:water"], contextual_source_refs=["cross-lingual-exchange:reference"],
        rationale="Retain synthetic anomaly for contextual investigation only; anomaly status is not evidence or wrongdoing.", reviewed_at="2026-09-29T04:00:00-05:00")
    evaluation=GraphAnomalyEvaluationRecord(
        anomaly_evaluation_id="graph-anomaly-evaluation:reference:v1", anomaly_task_ref=task.anomaly_task_id,
        detector_binding_ref=binding.detector_binding_id, evaluation_run_ref="graph-anomaly-eval-run:reference:v1",
        dataset_partition_ref="dataset-partition:reference:anomaly-test", metric_values={"auroc":.88,"average_precision":.81,"false_positive_rate":.07},
        threshold_policy_ref=task.threshold_policy_ref, calibration_artifact_ref="calibration:reference:anomaly:v1")
    return GraphAnomalyDetectionBundle(graph_link_prediction_bundle=lp,tasks=[task],runtime_contracts=[runtime],detector_bindings=[binding],targets=[target],scores=[score],explanations=[explanation],reviews=[review],evaluations=[evaluation],metadata={"reference_fixture":"synthetic-contract-fixture","anomaly_is_not_evidence":True,"anomaly_is_not_wrongdoing":True})


def contract_document() -> dict[str,Any]:
    b=reference_graph_anomaly_detection_bundle()
    return {
        "ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,
        "extends_contracts":["sc.core.graph-machine-learning-foundation.v1","sc.core.graph-embedding-runtime.v1","sc.core.graph-node-edge-classification.v1","sc.core.graph-link-prediction-candidate-relationship.v1"],
        "object_types":["GraphAnomalyDetectionTask","GraphAnomalyRuntimeContract","GraphAnomalyDetectorBinding","GraphAnomalyTarget","GraphAnomalyScoreRecord","GraphAnomalyExplanationRecord","GraphAnomalyReviewRecord","GraphAnomalyEvaluationRecord","GraphAnomalyDetectionBundle"],
        "principles":{
            "anomaly_detection_is_derived_model_output":True,"anomaly_is_not_graph_fact":True,"anomaly_is_not_evidence":True,"anomaly_is_not_wrongdoing":True,"anomaly_score_is_not_evidence_strength":True,"high_anomaly_score_does_not_establish_error":True,"embedding_outlier_does_not_establish_wrongdoing":True,"structural_outlier_does_not_establish_invalid_edge":True,"human_review_does_not_create_evidence_edge":True,"contradicting_context_must_remain_visible":True,"gnn_prediction_is_not_graph_fact":True},
        "boundaries":{
            "core_trains_anomaly_detector":False,"core_runs_anomaly_detection_inference":False,"core_labels_wrongdoing_from_anomaly":False,"core_mutates_evidence_graph_from_anomaly":False,"core_deletes_nodes_or_edges_from_anomaly":False,"core_promotes_anomaly_to_evidence":False,"runtime_may_mutate_evidence_graph":False,"runtime_may_assert_wrongdoing":False,"v374_determines_anomaly_truth":False},
        "review_requirements":{"contextual_review_required":True,"supporting_and_contradicting_material_may_be_attached":True,"model_and_runtime_provenance_required":True,"threshold_policy_required":True,"anomaly_remains_non_evidentiary_after_review":True},
        "roadmap_integration":{"extends_v370_graph_ml_foundation":True,"extends_v371_graph_embedding_runtime":True,"extends_v372_node_edge_classification":True,"extends_v373_link_prediction_candidates":True,"prepares_v3750_knowledge_graph_representation_learning":True,"prepares_v3760_evidence_graph_neural_analysis_validation_workflow":True},
        "reference":{"tasks":len(b.tasks),"targets":len(b.targets),"scores":len(b.scores),"explanations":len(b.explanations),"reviews":len(b.reviews),"evaluations":len(b.evaluations),"bundle_fingerprint_sha256":b.fingerprint()}}
