from __future__ import annotations

import math
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .graph_machine_learning import GraphTargetKind, GraphMLTaskKind
from .graph_embedding_runtime import GraphEmbeddingBundle, reference_graph_embedding_bundle
from .machine_learning_models import ExecutionHost

CORE_RELEASE = "3.72.0"
CONTRACT_VERSION = "sc.core.graph-node-edge-classification.v1"


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


class ClassificationReviewState(str, Enum):
    predicted = "predicted"
    under_review = "under-review"
    human_reviewed = "human-reviewed"
    accepted_as_annotation = "accepted-as-annotation"
    rejected = "rejected"
    disputed = "disputed"


class ClassificationCalibrationState(str, Enum):
    uncalibrated = "uncalibrated"
    calibrated = "calibrated"
    calibration_unknown = "calibration-unknown"


class GraphClassLabelDefinition(BaseModel):
    label_id: str = Field(min_length=2, max_length=500)
    display_name: str = Field(min_length=1, max_length=300)
    description: str | None = Field(default=None, max_length=2000)
    ontology_ref: str | None = Field(default=None, max_length=1000)
    parent_label_refs: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    label_definition_is_not_graph_fact: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_label(self):
        _unique(self.parent_label_refs, "parent_label_refs")
        _unique(self.source_refs, "source_refs")
        if self.label_id in self.parent_label_refs:
            raise ValueError("label cannot be its own parent")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class GraphClassificationLabelSpace(BaseModel):
    label_space_id: str = Field(min_length=2, max_length=500)
    target_kind: GraphTargetKind
    labels: list[GraphClassLabelDefinition] = Field(min_length=2)
    mutually_exclusive: bool = True
    multi_label_allowed: bool = False
    open_set_unknown_allowed: bool = False
    unknown_label_ref: str | None = Field(default=None, max_length=500)
    version: str = Field(min_length=1, max_length=120)
    label_space_is_descriptive_not_evidentiary: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_space(self):
        ids=[x.label_id for x in self.labels]
        _unique(ids, "classification label ids")
        if self.mutually_exclusive and self.multi_label_allowed:
            raise ValueError("mutually exclusive label space cannot allow multi-label output")
        if self.unknown_label_ref and self.unknown_label_ref not in ids:
            raise ValueError("unknown_label_ref must resolve to a label in the label space")
        if self.target_kind not in {GraphTargetKind.node, GraphTargetKind.edge}:
            raise ValueError("v3.72 classification label spaces support node or edge targets only")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class GraphClassificationTask(BaseModel):
    classification_task_id: str = Field(min_length=2, max_length=500)
    graph_ml_task_kind: GraphMLTaskKind
    target_kind: GraphTargetKind
    snapshot_ref: str = Field(min_length=2, max_length=500)
    label_space_ref: str = Field(min_length=2, max_length=500)
    graph_ml_model_foundation_ref: str = Field(min_length=2, max_length=500)
    feature_binding_refs: list[str] = Field(default_factory=list)
    embedding_space_refs: list[str] = Field(default_factory=list)
    leakage_control_refs: list[str] = Field(default_factory=list)
    task_definition_is_not_evidence: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_task(self):
        expected = GraphMLTaskKind.node_classification if self.target_kind == GraphTargetKind.node else GraphMLTaskKind.edge_classification
        if self.graph_ml_task_kind != expected:
            raise ValueError("classification task kind must match target kind")
        for vals,label in ((self.feature_binding_refs,"feature_binding_refs"),(self.embedding_space_refs,"embedding_space_refs"),(self.leakage_control_refs,"leakage_control_refs")):
            _unique(vals,label)
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class GraphClassificationRuntimeContract(BaseModel):
    classification_runtime_contract_id: str = Field(min_length=2, max_length=500)
    extends_graph_ml_runtime_ref: str = Field(min_length=2, max_length=500)
    execution_host: ExecutionHost
    framework: str = Field(min_length=1, max_length=240)
    framework_version: str | None = Field(default=None, max_length=120)
    supported_target_kinds: list[GraphTargetKind] = Field(min_length=1)
    emits_class_probabilities: bool = True
    supports_calibration_metadata: bool = True
    core_executes_classifier: Literal[False] = False
    runtime_may_mutate_evidence_graph: Literal[False] = False
    runtime_may_promote_classification_to_graph_fact: Literal[False] = False
    arbitrary_code_allowed_by_core: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_runtime(self):
        vals=[x.value for x in self.supported_target_kinds]
        _unique(vals,"supported_target_kinds")
        if any(x not in {GraphTargetKind.node,GraphTargetKind.edge} for x in self.supported_target_kinds):
            raise ValueError("classification runtime supports node/edge targets only")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class GraphClassificationModelBinding(BaseModel):
    classification_model_binding_id: str = Field(min_length=2, max_length=500)
    graph_ml_model_foundation_ref: str = Field(min_length=2, max_length=500)
    classification_task_refs: list[str] = Field(min_length=1)
    classification_runtime_contract_ref: str = Field(min_length=2, max_length=500)
    checkpoint_ref: str | None = Field(default=None, max_length=1000)
    training_run_ref: str = Field(min_length=2, max_length=500)
    evaluation_refs: list[str] = Field(default_factory=list)
    calibration_refs: list[str] = Field(default_factory=list)
    model_binding_is_not_model_validation: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_binding(self):
        _unique(self.classification_task_refs,"classification_task_refs")
        _unique(self.evaluation_refs,"evaluation_refs")
        _unique(self.calibration_refs,"calibration_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class GraphClassProbability(BaseModel):
    label_ref: str = Field(min_length=2, max_length=500)
    probability: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_probability(self):
        if not math.isfinite(self.probability):
            raise ValueError("classification probability must be finite")
        return self


class GraphClassificationPrediction(BaseModel):
    classification_prediction_id: str = Field(min_length=2, max_length=500)
    target_kind: GraphTargetKind
    target_object_ref: str = Field(min_length=2, max_length=1000)
    snapshot_ref: str = Field(min_length=2, max_length=500)
    classification_task_ref: str = Field(min_length=2, max_length=500)
    label_space_ref: str = Field(min_length=2, max_length=500)
    model_binding_ref: str = Field(min_length=2, max_length=500)
    inference_run_ref: str = Field(min_length=2, max_length=500)
    class_probabilities: list[GraphClassProbability] = Field(min_length=2)
    predicted_label_refs: list[str] = Field(min_length=1)
    calibration_state: ClassificationCalibrationState = ClassificationCalibrationState.calibration_unknown
    calibration_ref: str | None = Field(default=None, max_length=1000)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    feature_binding_refs: list[str] = Field(default_factory=list)
    embedding_refs: list[str] = Field(default_factory=list)
    explanation_refs: list[str] = Field(default_factory=list)
    review_state: ClassificationReviewState = ClassificationReviewState.predicted
    reviewer_ref: str | None = Field(default=None, max_length=1000)
    is_graph_fact: Literal[False] = False
    is_evidence: Literal[False] = False
    is_evidence_edge: Literal[False] = False
    classification_does_not_change_target_identity: Literal[True] = True
    requires_separate_validation_before_graph_fact: Literal[True] = True
    high_probability_does_not_establish_truth: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_prediction(self):
        if self.target_kind not in {GraphTargetKind.node, GraphTargetKind.edge}:
            raise ValueError("classification prediction target must be node or edge")
        labels=[x.label_ref for x in self.class_probabilities]
        _unique(labels,"class probability label refs")
        _unique(self.predicted_label_refs,"predicted_label_refs")
        if not set(self.predicted_label_refs).issubset(set(labels)):
            raise ValueError("predicted labels must appear in class probabilities")
        if self.calibration_state == ClassificationCalibrationState.calibrated and not self.calibration_ref:
            raise ValueError("calibrated prediction requires calibration_ref")
        if self.review_state != ClassificationReviewState.predicted and not self.reviewer_ref:
            raise ValueError("reviewed classification requires reviewer_ref")
        for vals,label in ((self.feature_binding_refs,"feature_binding_refs"),(self.embedding_refs,"embedding_refs"),(self.explanation_refs,"explanation_refs")):
            _unique(vals,label)
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class GraphClassificationEvaluationRecord(BaseModel):
    classification_evaluation_id: str = Field(min_length=2, max_length=500)
    classification_task_ref: str = Field(min_length=2, max_length=500)
    model_binding_ref: str = Field(min_length=2, max_length=500)
    label_space_ref: str = Field(min_length=2, max_length=500)
    evaluation_run_ref: str = Field(min_length=2, max_length=500)
    dataset_partition_ref: str = Field(min_length=2, max_length=1000)
    metric_values: dict[str, float] = Field(min_length=1)
    per_class_metric_artifact_ref: str | None = Field(default=None, max_length=1000)
    confusion_matrix_artifact_ref: str | None = Field(default=None, max_length=1000)
    calibration_artifact_ref: str | None = Field(default=None, max_length=1000)
    evaluation_metrics_are_descriptive_not_evidence: Literal[True] = True
    evaluation_does_not_rank_truth: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_eval(self):
        for k,v in self.metric_values.items():
            if not k or not math.isfinite(v):
                raise ValueError("evaluation metrics require nonempty names and finite values")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class GraphClassificationBundle(BaseModel):
    graph_embedding_bundle: GraphEmbeddingBundle
    label_spaces: list[GraphClassificationLabelSpace] = Field(min_length=2)
    tasks: list[GraphClassificationTask] = Field(min_length=2)
    runtime_contracts: list[GraphClassificationRuntimeContract] = Field(min_length=1)
    model_bindings: list[GraphClassificationModelBinding] = Field(min_length=1)
    predictions: list[GraphClassificationPrediction] = Field(min_length=2)
    evaluations: list[GraphClassificationEvaluationRecord] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_bundle(self):
        for xs,label,attr in ((self.label_spaces,"label spaces","label_space_id"),(self.tasks,"tasks","classification_task_id"),(self.runtime_contracts,"runtime contracts","classification_runtime_contract_id"),(self.model_bindings,"model bindings","classification_model_binding_id"),(self.predictions,"predictions","classification_prediction_id"),(self.evaluations,"evaluations","classification_evaluation_id")):
            _unique([getattr(x,attr) for x in xs],label)
        spaces={x.label_space_id:x for x in self.label_spaces}
        tasks={x.classification_task_id:x for x in self.tasks}
        runtimes={x.classification_runtime_contract_id for x in self.runtime_contracts}
        bindings={x.classification_model_binding_id:x for x in self.model_bindings}
        snapshots={x.snapshot_id:x for x in self.graph_embedding_bundle.graph_ml_foundation_bundle.snapshots}
        embedding_ids={x.embedding_id for x in self.graph_embedding_bundle.embeddings}
        for t in self.tasks:
            if t.label_space_ref not in spaces: raise ValueError("task label space must resolve")
            if t.snapshot_ref not in snapshots: raise ValueError("task snapshot must resolve")
            if spaces[t.label_space_ref].target_kind != t.target_kind: raise ValueError("task target kind must match label space")
        for b in self.model_bindings:
            if b.classification_runtime_contract_ref not in runtimes: raise ValueError("model binding runtime must resolve")
            if any(x not in tasks for x in b.classification_task_refs): raise ValueError("model binding tasks must resolve")
        for p in self.predictions:
            if p.classification_task_ref not in tasks or p.label_space_ref not in spaces or p.model_binding_ref not in bindings: raise ValueError("prediction references must resolve")
            task=tasks[p.classification_task_ref]; space=spaces[p.label_space_ref]; snap=snapshots[p.snapshot_ref]
            if p.target_kind != task.target_kind or p.target_kind != space.target_kind: raise ValueError("prediction target kind mismatch")
            known_labels={x.label_id for x in space.labels}
            if any(x.label_ref not in known_labels for x in p.class_probabilities): raise ValueError("prediction probability labels must resolve")
            if space.mutually_exclusive:
                total=sum(x.probability for x in p.class_probabilities)
                if not math.isclose(total,1.0,rel_tol=1e-6,abs_tol=1e-6): raise ValueError("exclusive class probabilities must sum to 1")
                maxp=max(x.probability for x in p.class_probabilities)
                winners={x.label_ref for x in p.class_probabilities if math.isclose(x.probability,maxp,rel_tol=1e-12,abs_tol=1e-12)}
                if len(p.predicted_label_refs)!=1 or p.predicted_label_refs[0] not in winners: raise ValueError("exclusive prediction must choose a maximum-probability label")
            if p.target_kind == GraphTargetKind.node and p.target_object_ref not in snap.node_refs: raise ValueError("node classification target must resolve to snapshot node")
            if p.target_kind == GraphTargetKind.edge and p.target_object_ref not in {e.evidence_edge_ref for e in snap.evidence_edges}: raise ValueError("edge classification target must resolve to existing snapshot evidence edge")
            if any(x not in embedding_ids for x in p.embedding_refs): raise ValueError("prediction embedding refs must resolve")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


def reference_graph_classification_bundle() -> GraphClassificationBundle:
    eb=reference_graph_embedding_bundle()
    g=eb.graph_ml_foundation_bundle
    node_space=GraphClassificationLabelSpace(
        label_space_id="graph-label-space:reference:node-role:v1", target_kind=GraphTargetKind.node, version="1",
        labels=[GraphClassLabelDefinition(label_id="node-class:concept-anchor",display_name="Concept anchor"),GraphClassLabelDefinition(label_id="node-class:other",display_name="Other")])
    edge_space=GraphClassificationLabelSpace(
        label_space_id="graph-label-space:reference:edge-role:v1", target_kind=GraphTargetKind.edge, version="1",
        labels=[GraphClassLabelDefinition(label_id="edge-class:source-cooccurrence",display_name="Source co-occurrence"),GraphClassLabelDefinition(label_id="edge-class:other",display_name="Other")])
    model_ref=g.model_foundations[0].foundation_id
    snap=g.snapshots[0].snapshot_id
    tasks=[
        GraphClassificationTask(classification_task_id="graph-classification-task:reference:node:v1",graph_ml_task_kind=GraphMLTaskKind.node_classification,target_kind=GraphTargetKind.node,snapshot_ref=snap,label_space_ref=node_space.label_space_id,graph_ml_model_foundation_ref=model_ref,embedding_space_refs=[eb.embedding_spaces[0].embedding_space_id]),
        GraphClassificationTask(classification_task_id="graph-classification-task:reference:edge:v1",graph_ml_task_kind=GraphMLTaskKind.edge_classification,target_kind=GraphTargetKind.edge,snapshot_ref=snap,label_space_ref=edge_space.label_space_id,graph_ml_model_foundation_ref=model_ref),
    ]
    runtime=GraphClassificationRuntimeContract(classification_runtime_contract_id="graph-classification-runtime:reference:v1",extends_graph_ml_runtime_ref=g.runtime_contracts[0].runtime_contract_id,execution_host=ExecutionHost.workspace,framework="pytorch-geometric",framework_version="reference",supported_target_kinds=[GraphTargetKind.node,GraphTargetKind.edge])
    binding=GraphClassificationModelBinding(classification_model_binding_id="graph-classification-model-binding:reference:v1",graph_ml_model_foundation_ref=model_ref,classification_task_refs=[x.classification_task_id for x in tasks],classification_runtime_contract_ref=runtime.classification_runtime_contract_id,training_run_ref=g.run_provenance[0].run_id,evaluation_refs=["graph-classification-evaluation:reference:v1"],calibration_refs=["calibration:reference:temperature:v1"])
    preds=[
        GraphClassificationPrediction(classification_prediction_id="graph-classification-prediction:reference:node-en:v1",target_kind=GraphTargetKind.node,target_object_ref=g.snapshots[0].node_refs[0],snapshot_ref=snap,classification_task_ref=tasks[0].classification_task_id,label_space_ref=node_space.label_space_id,model_binding_ref=binding.classification_model_binding_id,inference_run_ref=g.run_provenance[1].run_id,class_probabilities=[GraphClassProbability(label_ref="node-class:concept-anchor",probability=.94),GraphClassProbability(label_ref="node-class:other",probability=.06)],predicted_label_refs=["node-class:concept-anchor"],calibration_state=ClassificationCalibrationState.calibrated,calibration_ref="calibration:reference:temperature:v1",confidence=.94,embedding_refs=[eb.embeddings[0].embedding_id]),
        GraphClassificationPrediction(classification_prediction_id="graph-classification-prediction:reference:edge-en-zh:v1",target_kind=GraphTargetKind.edge,target_object_ref=g.snapshots[0].evidence_edges[0].evidence_edge_ref,snapshot_ref=snap,classification_task_ref=tasks[1].classification_task_id,label_space_ref=edge_space.label_space_id,model_binding_ref=binding.classification_model_binding_id,inference_run_ref=g.run_provenance[1].run_id,class_probabilities=[GraphClassProbability(label_ref="edge-class:source-cooccurrence",probability=.88),GraphClassProbability(label_ref="edge-class:other",probability=.12)],predicted_label_refs=["edge-class:source-cooccurrence"],confidence=.88),
    ]
    evaluation=GraphClassificationEvaluationRecord(classification_evaluation_id="graph-classification-evaluation:reference:v1",classification_task_ref=tasks[0].classification_task_id,model_binding_ref=binding.classification_model_binding_id,label_space_ref=node_space.label_space_id,evaluation_run_ref="graph-classification-eval-run:reference:v1",dataset_partition_ref="dataset-partition:reference:test",metric_values={"accuracy":.91,"macro_f1":.89},calibration_artifact_ref="calibration:reference:temperature:v1")
    return GraphClassificationBundle(graph_embedding_bundle=eb,label_spaces=[node_space,edge_space],tasks=tasks,runtime_contracts=[runtime],model_bindings=[binding],predictions=preds,evaluations=[evaluation],metadata={"reference_fixture":"synthetic-contract-fixture"})


def contract_document() -> dict[str, Any]:
    b=reference_graph_classification_bundle()
    return {
        "ok": True, "release": CORE_RELEASE, "contract": CONTRACT_VERSION,
        "extends_contracts": ["sc.core.graph-machine-learning-foundation.v1","sc.core.graph-embedding-runtime.v1"],
        "object_types": ["GraphClassLabelDefinition","GraphClassificationLabelSpace","GraphClassificationTask","GraphClassificationRuntimeContract","GraphClassificationModelBinding","GraphClassProbability","GraphClassificationPrediction","GraphClassificationEvaluationRecord","GraphClassificationBundle"],
        "principles": {
            "classification_output_is_derived_model_output": True,
            "node_classification_is_not_graph_fact": True,
            "edge_classification_is_not_graph_fact": True,
            "classification_probability_is_not_evidence_strength": True,
            "high_probability_does_not_establish_truth": True,
            "reviewed_classification_remains_distinct_from_evidence": True,
            "classification_does_not_change_target_identity": True,
            "gnn_prediction_is_not_graph_fact": True,
        },
        "boundaries": {
            "core_trains_graph_classifier": False,
            "core_runs_graph_classification_inference": False,
            "core_calibrates_classifier": False,
            "core_promotes_classification_to_graph_fact": False,
            "core_mutates_node_or_edge_identity_from_classification": False,
            "runtime_may_mutate_evidence_graph": False,
            "runtime_may_promote_classification_to_graph_fact": False,
            "v372_performs_link_prediction": False,
        },
        "roadmap_integration": {
            "extends_v370_graph_ml_foundation": True,
            "extends_v371_graph_embedding_runtime": True,
            "prepares_v3730_link_prediction_candidate_relationship_objects": True,
            "prepares_v3740_graph_anomaly_detection": True,
            "prepares_v3750_knowledge_graph_representation_learning": True,
            "prepares_v3760_evidence_graph_neural_analysis_validation_workflow": True,
        },
        "reference": {"label_spaces":len(b.label_spaces),"tasks":len(b.tasks),"predictions":len(b.predictions),"evaluations":len(b.evaluations),"bundle_fingerprint_sha256":b.fingerprint()}
    }
