from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .cross_lingual_semantic_exchange import (
    CrossLingualSemanticExchangeBundle,
    reference_cross_lingual_semantic_exchange_bundle,
)
from .machine_learning_models import (
    ExecutionHost,
    FeatureDataType,
    LearningParadigm,
    MLFeatureSchema,
    MLFeatureSpec,
    MLModelFamily,
    MLModelSpecification,
    MLObjectiveSpec,
    MLRuntimeBinding,
    MLTaskKind,
    NeuralArchitectureKind,
    NeuralArchitectureSpec,
    NeuralLayerSpec,
)

CORE_RELEASE = "3.70.0"
CONTRACT_VERSION = "sc.core.graph-machine-learning-foundation.v1"


class GraphMLTaskKind(str, Enum):
    graph_classification = "graph-classification"
    node_classification = "node-classification"
    edge_classification = "edge-classification"
    link_prediction = "link-prediction"
    anomaly_detection = "anomaly-detection"
    representation_learning = "representation-learning"


class GraphLearningMode(str, Enum):
    transductive = "transductive"
    inductive = "inductive"
    hybrid = "hybrid"


class GraphTargetKind(str, Enum):
    node = "node"
    edge = "edge"
    graph = "graph"


class GraphRunKind(str, Enum):
    train = "train"
    evaluate = "evaluate"
    infer = "infer"
    embed = "embed"


class RelationshipPredictionState(str, Enum):
    predicted = "predicted"
    under_review = "under-review"
    rejected = "rejected"
    disputed = "disputed"


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


class GraphEvidenceEdgeBinding(BaseModel):
    evidence_edge_ref: str = Field(min_length=2, max_length=1000)
    source_node_ref: str = Field(min_length=2, max_length=1000)
    target_node_ref: str = Field(min_length=2, max_length=1000)
    relationship_type: str = Field(min_length=1, max_length=300)
    evidence_refs: list[str] = Field(min_length=1)
    provenance_refs: list[str] = Field(min_length=1)
    validated_before_graph_snapshot: Literal[True] = True
    generated_by_graph_ml_model: Literal[False] = False
    prediction_score_is_not_evidence: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_edge(self):
        if self.source_node_ref == self.target_node_ref:
            raise ValueError("graph evidence edge cannot be self-referential")
        _unique(self.evidence_refs, "evidence edge evidence_refs")
        _unique(self.provenance_refs, "evidence edge provenance_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class GraphLearningSnapshot(BaseModel):
    snapshot_id: str = Field(min_length=2, max_length=500)
    source_graph_ref: str = Field(min_length=2, max_length=1000)
    source_graph_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    node_refs: list[str] = Field(min_length=2)
    evidence_edges: list[GraphEvidenceEdgeBinding] = Field(default_factory=list)
    excluded_candidate_relationship_refs: list[str] = Field(default_factory=list)
    created_at: str | None = Field(default=None, max_length=80)
    immutable_snapshot: Literal[True] = True
    predicted_relationships_are_excluded_from_evidence_edges: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_snapshot(self):
        _unique(self.node_refs, "graph snapshot node_refs")
        _unique([x.evidence_edge_ref for x in self.evidence_edges], "graph snapshot evidence edge refs")
        _unique(self.excluded_candidate_relationship_refs, "excluded candidate relationship refs")
        known = set(self.node_refs)
        for edge in self.evidence_edges:
            if edge.source_node_ref not in known or edge.target_node_ref not in known:
                raise ValueError("graph evidence edge endpoints must resolve to snapshot node_refs")
            if edge.evidence_edge_ref in self.excluded_candidate_relationship_refs:
                raise ValueError("predicted/candidate relationship cannot also be an evidence edge")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class GraphFeatureBinding(BaseModel):
    feature_binding_id: str = Field(min_length=2, max_length=500)
    snapshot_ref: str = Field(min_length=2, max_length=500)
    target_kind: GraphTargetKind
    object_refs: list[str] = Field(min_length=1)
    feature_schema_ref: str = Field(min_length=2, max_length=500)
    feature_artifact_ref: str = Field(min_length=2, max_length=1000)
    feature_artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_refs: list[str] = Field(min_length=1)
    transformation_refs: list[str] = Field(default_factory=list)
    cross_lingual_exchange_refs: list[str] = Field(default_factory=list)
    feature_values_are_not_evidence: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_binding(self):
        _unique(self.object_refs, "feature binding object_refs")
        _unique(self.source_refs, "feature binding source_refs")
        _unique(self.transformation_refs, "feature binding transformation_refs")
        _unique(self.cross_lingual_exchange_refs, "feature binding cross_lingual_exchange_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class GraphLabelBinding(BaseModel):
    label_binding_id: str = Field(min_length=2, max_length=500)
    snapshot_ref: str = Field(min_length=2, max_length=500)
    target_kind: GraphTargetKind
    object_refs: list[str] = Field(min_length=1)
    label_artifact_ref: str = Field(min_length=2, max_length=1000)
    label_artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_evidence_refs: list[str] = Field(default_factory=list)
    source_annotation_refs: list[str] = Field(default_factory=list)
    weak_or_heuristic_labels_advisory: Literal[True] = True
    labels_do_not_create_graph_facts: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_labels(self):
        _unique(self.object_refs, "label binding object_refs")
        _unique(self.source_evidence_refs, "label binding source_evidence_refs")
        _unique(self.source_annotation_refs, "label binding source_annotation_refs")
        if not self.source_evidence_refs and not self.source_annotation_refs:
            raise ValueError("graph label binding requires evidence or annotation provenance")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class GraphMLTaskSpecification(BaseModel):
    task_id: str = Field(min_length=2, max_length=500)
    task_kind: GraphMLTaskKind
    learning_mode: GraphLearningMode
    snapshot_ref: str = Field(min_length=2, max_length=500)
    model_spec_ref: str = Field(min_length=2, max_length=500)
    feature_binding_refs: list[str] = Field(min_length=1)
    label_binding_refs: list[str] = Field(default_factory=list)
    target_relationship_types: list[str] = Field(default_factory=list)
    negative_sampling_policy_ref: str | None = Field(default=None, max_length=1000)
    leakage_control_refs: list[str] = Field(default_factory=list)
    task_definition_is_not_evidence: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_task(self):
        _unique(self.feature_binding_refs, "graph task feature_binding_refs")
        _unique(self.label_binding_refs, "graph task label_binding_refs")
        _unique(self.target_relationship_types, "graph task target_relationship_types")
        _unique(self.leakage_control_refs, "graph task leakage_control_refs")
        if self.task_kind in {GraphMLTaskKind.node_classification, GraphMLTaskKind.edge_classification, GraphMLTaskKind.link_prediction} and not self.label_binding_refs:
            raise ValueError("supervised graph task requires label_binding_refs")
        if self.task_kind == GraphMLTaskKind.link_prediction and not self.target_relationship_types:
            raise ValueError("link prediction task requires target_relationship_types")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class GraphMLRuntimeContract(BaseModel):
    runtime_contract_id: str = Field(min_length=2, max_length=500)
    model_spec_ref: str = Field(min_length=2, max_length=500)
    runtime_binding_ref: str = Field(min_length=2, max_length=500)
    execution_host: ExecutionHost
    framework: str = Field(min_length=1, max_length=240)
    framework_version: str | None = Field(default=None, max_length=120)
    supported_operations: list[GraphRunKind] = Field(min_length=1)
    required_capabilities: list[str] = Field(default_factory=list)
    core_executes_graph_ml: Literal[False] = False
    runtime_may_mutate_evidence_graph: Literal[False] = False
    arbitrary_code_allowed_by_core: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_runtime(self):
        _unique([x.value for x in self.supported_operations], "graph runtime supported_operations")
        _unique(self.required_capabilities, "graph runtime required_capabilities")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class GraphMLModelFoundation(BaseModel):
    foundation_id: str = Field(min_length=2, max_length=500)
    model_spec: MLModelSpecification
    registry_entry_ref: str | None = Field(default=None, max_length=500)
    graph_task_refs: list[str] = Field(min_length=1)
    runtime_contract_refs: list[str] = Field(min_length=1)
    graph_snapshot_refs: list[str] = Field(min_length=1)
    framework_neutral: Literal[True] = True
    model_definition_is_not_model_validation: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_foundation(self):
        if self.model_spec.model_family != MLModelFamily.graph_neural_network:
            raise ValueError("Graph ML foundation requires graph-neural-network model family")
        if not self.model_spec.neural_architecture or self.model_spec.neural_architecture.architecture_kind != NeuralArchitectureKind.graph_neural_network:
            raise ValueError("Graph ML foundation requires graph-neural-network architecture")
        _unique(self.graph_task_refs, "foundation graph_task_refs")
        _unique(self.runtime_contract_refs, "foundation runtime_contract_refs")
        _unique(self.graph_snapshot_refs, "foundation graph_snapshot_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class GraphMLRunProvenance(BaseModel):
    run_id: str = Field(min_length=2, max_length=500)
    run_kind: GraphRunKind
    task_ref: str = Field(min_length=2, max_length=500)
    model_spec_ref: str = Field(min_length=2, max_length=500)
    runtime_contract_ref: str = Field(min_length=2, max_length=500)
    snapshot_ref: str = Field(min_length=2, max_length=500)
    input_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    output_artifact_refs: list[str] = Field(min_length=1)
    environment_ref: str | None = Field(default=None, max_length=500)
    created_at: str | None = Field(default=None, max_length=80)
    run_output_is_not_evidence: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_run(self):
        _unique(self.output_artifact_refs, "graph run output_artifact_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class PredictedRelationship(BaseModel):
    prediction_id: str = Field(min_length=2, max_length=500)
    source_node_ref: str = Field(min_length=2, max_length=1000)
    target_node_ref: str = Field(min_length=2, max_length=1000)
    relationship_type_candidate: str = Field(min_length=1, max_length=300)
    inference_run_ref: str = Field(min_length=2, max_length=500)
    model_spec_ref: str = Field(min_length=2, max_length=500)
    score: float | None = Field(default=None)
    probability: float | None = Field(default=None, ge=0.0, le=1.0)
    feature_binding_refs: list[str] = Field(default_factory=list)
    training_lineage_refs: list[str] = Field(default_factory=list)
    calibration_refs: list[str] = Field(default_factory=list)
    explanation_refs: list[str] = Field(default_factory=list)
    supporting_evidence_refs: list[str] = Field(default_factory=list)
    contradicting_evidence_refs: list[str] = Field(default_factory=list)
    state: RelationshipPredictionState = RelationshipPredictionState.predicted
    reviewer_ref: str | None = Field(default=None, max_length=1000)
    is_graph_fact: Literal[False] = False
    is_evidence_edge: Literal[False] = False
    requires_separate_validation_before_evidence_edge: Literal[True] = True
    high_score_does_not_establish_truth: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_prediction(self):
        if self.source_node_ref == self.target_node_ref:
            raise ValueError("predicted relationship cannot be self-referential")
        for values, label in (
            (self.feature_binding_refs, "prediction feature_binding_refs"),
            (self.training_lineage_refs, "prediction training_lineage_refs"),
            (self.calibration_refs, "prediction calibration_refs"),
            (self.explanation_refs, "prediction explanation_refs"),
            (self.supporting_evidence_refs, "prediction supporting_evidence_refs"),
            (self.contradicting_evidence_refs, "prediction contradicting_evidence_refs"),
        ):
            _unique(values, label)
        if self.state != RelationshipPredictionState.predicted and not self.reviewer_ref:
            raise ValueError("reviewed/rejected/disputed relationship prediction requires reviewer_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class GraphMLFoundationBundle(BaseModel):
    cross_lingual_exchange_bundle: CrossLingualSemanticExchangeBundle
    snapshots: list[GraphLearningSnapshot] = Field(min_length=1)
    feature_bindings: list[GraphFeatureBinding] = Field(min_length=1)
    label_bindings: list[GraphLabelBinding] = Field(min_length=1)
    tasks: list[GraphMLTaskSpecification] = Field(min_length=1)
    runtime_contracts: list[GraphMLRuntimeContract] = Field(min_length=1)
    model_foundations: list[GraphMLModelFoundation] = Field(min_length=1)
    run_provenance: list[GraphMLRunProvenance] = Field(min_length=1)
    predicted_relationships: list[PredictedRelationship] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_bundle(self):
        snapshots = {x.snapshot_id: x for x in self.snapshots}
        features = {x.feature_binding_id: x for x in self.feature_bindings}
        labels = {x.label_binding_id: x for x in self.label_bindings}
        tasks = {x.task_id: x for x in self.tasks}
        runtimes = {x.runtime_contract_id: x for x in self.runtime_contracts}
        foundations = {x.foundation_id: x for x in self.model_foundations}
        runs = {x.run_id: x for x in self.run_provenance}
        predictions = {x.prediction_id: x for x in self.predicted_relationships}

        for label, values in (
            ("snapshot ids", [x.snapshot_id for x in self.snapshots]),
            ("feature binding ids", [x.feature_binding_id for x in self.feature_bindings]),
            ("label binding ids", [x.label_binding_id for x in self.label_bindings]),
            ("task ids", [x.task_id for x in self.tasks]),
            ("runtime contract ids", [x.runtime_contract_id for x in self.runtime_contracts]),
            ("foundation ids", [x.foundation_id for x in self.model_foundations]),
            ("run ids", [x.run_id for x in self.run_provenance]),
            ("prediction ids", [x.prediction_id for x in self.predicted_relationships]),
        ):
            _unique(values, label)

        for binding in self.feature_bindings:
            snapshot = snapshots.get(binding.snapshot_ref)
            if snapshot is None:
                raise ValueError("feature binding snapshot_ref must resolve")
            if set(binding.object_refs) - set(snapshot.node_refs):
                raise ValueError("feature binding object_refs must resolve to snapshot node_refs")

        for binding in self.label_bindings:
            snapshot = snapshots.get(binding.snapshot_ref)
            if snapshot is None:
                raise ValueError("label binding snapshot_ref must resolve")
            if binding.target_kind == GraphTargetKind.node and set(binding.object_refs) - set(snapshot.node_refs):
                raise ValueError("node label binding object_refs must resolve to snapshot node_refs")
            if binding.target_kind == GraphTargetKind.edge:
                edge_refs = {x.evidence_edge_ref for x in snapshot.evidence_edges}
                if set(binding.object_refs) - edge_refs:
                    raise ValueError("edge label binding object_refs must resolve to evidence edges")

        model_specs = {x.model_spec.model_spec_id: x.model_spec for x in self.model_foundations}
        for task in self.tasks:
            if task.snapshot_ref not in snapshots:
                raise ValueError("graph task snapshot_ref must resolve")
            if task.model_spec_ref not in model_specs:
                raise ValueError("graph task model_spec_ref must resolve")
            if set(task.feature_binding_refs) - set(features):
                raise ValueError("graph task feature_binding_refs must resolve")
            if set(task.label_binding_refs) - set(labels):
                raise ValueError("graph task label_binding_refs must resolve")
            for ref in task.feature_binding_refs:
                if features[ref].snapshot_ref != task.snapshot_ref:
                    raise ValueError("graph task feature binding must use same snapshot")
            for ref in task.label_binding_refs:
                if labels[ref].snapshot_ref != task.snapshot_ref:
                    raise ValueError("graph task label binding must use same snapshot")

        for runtime in self.runtime_contracts:
            spec = model_specs.get(runtime.model_spec_ref)
            if spec is None:
                raise ValueError("graph runtime model_spec_ref must resolve")
            runtime_binding_ids = {x.runtime_binding_id for x in spec.runtime_bindings}
            if runtime.runtime_binding_ref not in runtime_binding_ids:
                raise ValueError("graph runtime runtime_binding_ref must resolve to model spec")

        for foundation in foundations.values():
            if set(foundation.graph_task_refs) - set(tasks):
                raise ValueError("foundation graph_task_refs must resolve")
            if set(foundation.runtime_contract_refs) - set(runtimes):
                raise ValueError("foundation runtime_contract_refs must resolve")
            if set(foundation.graph_snapshot_refs) - set(snapshots):
                raise ValueError("foundation graph_snapshot_refs must resolve")

        for run in self.run_provenance:
            task = tasks.get(run.task_ref)
            if task is None:
                raise ValueError("graph run task_ref must resolve")
            if run.model_spec_ref != task.model_spec_ref:
                raise ValueError("graph run model_spec_ref must match graph task")
            if run.snapshot_ref != task.snapshot_ref:
                raise ValueError("graph run snapshot_ref must match graph task")
            runtime = runtimes.get(run.runtime_contract_ref)
            if runtime is None or runtime.model_spec_ref != run.model_spec_ref:
                raise ValueError("graph run runtime_contract_ref must resolve to same model")

        all_evidence_edges = {edge.evidence_edge_ref for snapshot in self.snapshots for edge in snapshot.evidence_edges}
        all_nodes = {node for snapshot in self.snapshots for node in snapshot.node_refs}
        for prediction in predictions.values():
            run = runs.get(prediction.inference_run_ref)
            if run is None:
                raise ValueError("predicted relationship inference_run_ref must resolve")
            if prediction.model_spec_ref != run.model_spec_ref:
                raise ValueError("predicted relationship model_spec_ref must match inference run")
            if run.run_kind != GraphRunKind.infer:
                raise ValueError("predicted relationship requires inference run provenance")
            if prediction.source_node_ref not in all_nodes or prediction.target_node_ref not in all_nodes:
                raise ValueError("predicted relationship endpoints must resolve to graph snapshot nodes")
            if prediction.prediction_id in all_evidence_edges:
                raise ValueError("predicted relationship id cannot be an evidence edge ref")
            if set(prediction.feature_binding_refs) - set(features):
                raise ValueError("predicted relationship feature_binding_refs must resolve")

        for snapshot in self.snapshots:
            if set(snapshot.excluded_candidate_relationship_refs) - set(predictions):
                raise ValueError("snapshot excluded candidate relationship refs must resolve")
            evidence_refs = {x.evidence_edge_ref for x in snapshot.evidence_edges}
            if evidence_refs & set(snapshot.excluded_candidate_relationship_refs):
                raise ValueError("predicted/candidate relationships cannot be evidence edges")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


def _reference_graph_model_specification() -> MLModelSpecification:
    feature_schema = MLFeatureSchema(
        schema_id="ml-feature-schema:reference-graph-link:v1",
        features=[
            MLFeatureSpec(name="node_degree", data_type=FeatureDataType.floating, role="input"),
            MLFeatureSpec(name="semantic_embedding", data_type=FeatureDataType.embedding, role="input", shape=[8]),
            MLFeatureSpec(name="link_label", data_type=FeatureDataType.integer, role="target", category_labels=["0", "1"]),
        ],
        target_names=["link_label"],
        source_dataset_refs=["graph-snapshot:reference:v1"],
        metadata={"synthetic_reference": True, "graph_features_computed_outside_core": True},
    )
    architecture = NeuralArchitectureSpec(
        architecture_id="neural-architecture:reference-gnn-link:v1",
        architecture_kind=NeuralArchitectureKind.graph_neural_network,
        layers=[
            NeuralLayerSpec(layer_id="message-pass-1", layer_kind="graph-convolution", input_refs=["input:node-features", "input:evidence-edges"], activation="relu", output_shape=[16]),
            NeuralLayerSpec(layer_id="message-pass-2", layer_kind="graph-convolution", input_refs=["message-pass-1"], activation="relu", output_shape=[8]),
            NeuralLayerSpec(layer_id="link-score", layer_kind="pairwise-link-scorer", input_refs=["message-pass-2"], activation="sigmoid", output_shape=[1]),
        ],
        framework_hint="external-graph-ml-runtime",
        metadata={"synthetic_reference": True},
    )
    objective = MLObjectiveSpec(
        objective_id="ml-objective:reference-graph-link:v1",
        task=MLTaskKind.classification,
        learning_paradigm=LearningParadigm.supervised,
        loss_name="binary-cross-entropy",
        metric_names=["roc-auc", "average-precision"],
        optimization_direction="maximize",
        class_labels=["no-link", "candidate-link"],
        metadata={"graph_task_kind": GraphMLTaskKind.link_prediction.value},
    )
    runtime = MLRuntimeBinding(
        runtime_binding_id="ml-runtime-binding:reference-graph-pytorch:v1",
        adapter_id="adapter:sc-workspace-neural-runtime",
        runtime_id="sc-workspace-neural-runtime",
        execution_host=ExecutionHost.workspace,
        framework="pytorch-geometric-compatible",
        framework_version="external",
        environment_ref="environment:reference-graph-ml",
        supported_operations=["train", "evaluate", "infer", "embed", "export"],
        metadata={"core_executes": False},
    )
    return MLModelSpecification(
        model_spec_id="ml-model-spec:reference-graph-link-predictor:v1",
        ai_model_ref="ai-model:reference-graph-link-predictor",
        ai_model_version_ref="ai-model-version:reference-graph-link-predictor:1.0.0",
        model_family=MLModelFamily.graph_neural_network,
        algorithm_name="message-passing-graph-neural-network",
        feature_schema=feature_schema,
        objective=objective,
        neural_architecture=architecture,
        hyperparameters={"hidden_dimensions": [16, 8], "dropout": 0.1},
        runtime_bindings=[runtime],
        research_model_ref="research-model:reference-graph-link-predictor",
        provenance={"purpose": "Synthetic Platform Core v3.70 graph ML foundation reference"},
        metadata={"synthetic_reference": True, "not_quality_certification": True},
    )


def reference_graph_ml_foundation_bundle() -> GraphMLFoundationBundle:
    cross = reference_cross_lingual_semantic_exchange_bundle()
    anchors = {x.anchor_id: x for x in cross.anchors}
    en = anchors["anchor:reference:water:en"]
    zh = anchors["anchor:reference:water:zh"]
    es = anchors["anchor:reference:water:es"]
    source_ref = cross.translation_bundle.annotation_bundle.text_bundle.text_sources[0].text_source_id

    predicted_id = "predicted-relationship:reference:en-es:semantic-related"
    source_graph_payload = {
        "graph_ref": "research-graph:reference:linguistic-observation:v1",
        "nodes": [en.anchor_id, zh.anchor_id, es.anchor_id],
        "evidence_edges": ["evidence-edge:reference:en-zh:co-occurs-in-source"],
    }
    snapshot = GraphLearningSnapshot(
        snapshot_id="graph-snapshot:reference:v1",
        source_graph_ref=source_graph_payload["graph_ref"],
        source_graph_fingerprint_sha256=canonical_sha256(source_graph_payload),
        node_refs=source_graph_payload["nodes"],
        evidence_edges=[
            GraphEvidenceEdgeBinding(
                evidence_edge_ref=source_graph_payload["evidence_edges"][0],
                source_node_ref=en.anchor_id,
                target_node_ref=zh.anchor_id,
                relationship_type="co-occurs-in-reference-source",
                evidence_refs=[source_ref],
                provenance_refs=["provenance:reference-source-observation"],
                metadata={"synthetic_reference": True, "not_semantic_equivalence": True},
            )
        ],
        excluded_candidate_relationship_refs=[predicted_id],
        created_at="2026-09-29T01:20:00-05:00",
        metadata={"synthetic_reference": True},
    )

    spec = _reference_graph_model_specification()
    feature_binding = GraphFeatureBinding(
        feature_binding_id="graph-feature-binding:reference:nodes:v1",
        snapshot_ref=snapshot.snapshot_id,
        target_kind=GraphTargetKind.node,
        object_refs=snapshot.node_refs,
        feature_schema_ref=spec.feature_schema.schema_id,
        feature_artifact_ref="artifact:reference:graph-node-features:v1",
        feature_artifact_sha256=canonical_sha256({"fixture": "graph-node-features", "version": 1}),
        source_refs=[en.source_object_ref, zh.source_object_ref, es.source_object_ref],
        transformation_refs=["transformation:reference:graph-feature-materialization:v1"],
        cross_lingual_exchange_refs=[x.assertion_id for x in cross.assertions],
        metadata={"synthetic_reference": True, "computed_outside_core": True},
    )
    label_binding = GraphLabelBinding(
        label_binding_id="graph-label-binding:reference:links:v1",
        snapshot_ref=snapshot.snapshot_id,
        target_kind=GraphTargetKind.edge,
        object_refs=[snapshot.evidence_edges[0].evidence_edge_ref],
        label_artifact_ref="artifact:reference:graph-link-labels:v1",
        label_artifact_sha256=canonical_sha256({"fixture": "graph-link-labels", "version": 1}),
        source_evidence_refs=[snapshot.evidence_edges[0].evidence_edge_ref],
        metadata={"synthetic_reference": True, "negative_examples_are_sampling_artifacts": True},
    )
    task = GraphMLTaskSpecification(
        task_id="graph-ml-task:reference:link-prediction:v1",
        task_kind=GraphMLTaskKind.link_prediction,
        learning_mode=GraphLearningMode.transductive,
        snapshot_ref=snapshot.snapshot_id,
        model_spec_ref=spec.model_spec_id,
        feature_binding_refs=[feature_binding.feature_binding_id],
        label_binding_refs=[label_binding.label_binding_id],
        target_relationship_types=["semantic-related"],
        negative_sampling_policy_ref="policy:reference:graph-negative-sampling:v1",
        leakage_control_refs=["control:reference:no-test-edge-in-training:v1"],
        metadata={"synthetic_reference": True},
    )
    runtime = GraphMLRuntimeContract(
        runtime_contract_id="graph-ml-runtime-contract:reference:v1",
        model_spec_ref=spec.model_spec_id,
        runtime_binding_ref=spec.runtime_bindings[0].runtime_binding_id,
        execution_host=ExecutionHost.workspace,
        framework="pytorch-geometric-compatible",
        framework_version="external",
        supported_operations=[GraphRunKind.train, GraphRunKind.evaluate, GraphRunKind.infer, GraphRunKind.embed],
        required_capabilities=["message-passing", "graph-batching", "link-scoring"],
        metadata={"synthetic_reference": True, "workspace_computes": True},
    )
    foundation = GraphMLModelFoundation(
        foundation_id="graph-ml-foundation:reference:v1",
        model_spec=spec,
        registry_entry_ref=None,
        graph_task_refs=[task.task_id],
        runtime_contract_refs=[runtime.runtime_contract_id],
        graph_snapshot_refs=[snapshot.snapshot_id],
        metadata={"synthetic_reference": True, "registry_integration_prepared": True},
    )
    train_run = GraphMLRunProvenance(
        run_id="graph-ml-run:reference:train:v1",
        run_kind=GraphRunKind.train,
        task_ref=task.task_id,
        model_spec_ref=spec.model_spec_id,
        runtime_contract_ref=runtime.runtime_contract_id,
        snapshot_ref=snapshot.snapshot_id,
        input_fingerprint_sha256=snapshot.fingerprint(),
        output_artifact_refs=["artifact:reference:graph-model-checkpoint:v1"],
        environment_ref=spec.runtime_bindings[0].environment_ref,
        created_at="2026-09-29T01:21:00-05:00",
        metadata={"synthetic_reference": True},
    )
    infer_run = GraphMLRunProvenance(
        run_id="graph-ml-run:reference:infer:v1",
        run_kind=GraphRunKind.infer,
        task_ref=task.task_id,
        model_spec_ref=spec.model_spec_id,
        runtime_contract_ref=runtime.runtime_contract_id,
        snapshot_ref=snapshot.snapshot_id,
        input_fingerprint_sha256=snapshot.fingerprint(),
        output_artifact_refs=["artifact:reference:graph-link-predictions:v1"],
        environment_ref=spec.runtime_bindings[0].environment_ref,
        created_at="2026-09-29T01:22:00-05:00",
        metadata={"synthetic_reference": True},
    )
    prediction = PredictedRelationship(
        prediction_id=predicted_id,
        source_node_ref=en.anchor_id,
        target_node_ref=es.anchor_id,
        relationship_type_candidate="semantic-related",
        inference_run_ref=infer_run.run_id,
        model_spec_ref=spec.model_spec_id,
        score=2.31,
        probability=0.87,
        feature_binding_refs=[feature_binding.feature_binding_id],
        training_lineage_refs=[train_run.run_id],
        calibration_refs=["calibration:future-or-external:reference"],
        explanation_refs=["explanation:future-or-external:reference"],
        supporting_evidence_refs=["alignment:es-a:water"],
        state=RelationshipPredictionState.predicted,
        metadata={"synthetic_reference": True, "candidate_only": True, "not_promoted": True},
    )
    return GraphMLFoundationBundle(
        cross_lingual_exchange_bundle=cross,
        snapshots=[snapshot],
        feature_bindings=[feature_binding],
        label_bindings=[label_binding],
        tasks=[task],
        runtime_contracts=[runtime],
        model_foundations=[foundation],
        run_provenance=[train_run, infer_run],
        predicted_relationships=[prediction],
        metadata={
            "purpose": "Platform Core v3.70 graph machine learning foundation reference",
            "gnn_prediction_is_not_graph_fact": True,
            "predicted_relationship_requires_separate_validation_before_evidence_edge": True,
        },
    )


def contract_document() -> dict[str, Any]:
    ref = reference_graph_ml_foundation_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "extends_contracts": [
            "sc.core.machine-learning-neural-model-object.v1",
            "sc.core.neural-model-registry-reproducible-packages.v1",
            "sc.core.cross-lingual-semantic-linguistic-exchange.v1",
        ],
        "object_types": [
            "GraphEvidenceEdgeBinding",
            "GraphLearningSnapshot",
            "GraphFeatureBinding",
            "GraphLabelBinding",
            "GraphMLTaskSpecification",
            "GraphMLRuntimeContract",
            "GraphMLModelFoundation",
            "GraphMLRunProvenance",
            "PredictedRelationship",
            "GraphMLFoundationBundle",
        ],
        "task_kinds": [x.value for x in GraphMLTaskKind],
        "principles": {
            "gnn_prediction_is_not_graph_fact": True,
            "predicted_relationship_is_not_evidence_edge": True,
            "high_prediction_score_does_not_establish_truth": True,
            "predicted_relationship_requires_separate_validation_before_evidence_edge": True,
            "training_graph_distinguishes_evidence_edges_from_candidate_relationships": True,
            "graph_snapshot_is_immutable_and_provenance_bound": True,
            "weak_or_heuristic_labels_remain_advisory": True,
            "cross_lingual_assertion_remains_non_factual_until_separately_validated": True,
        },
        "capabilities": {
            "governed_graph_learning_snapshots": True,
            "evidence_edge_bindings": True,
            "node_edge_graph_feature_bindings": True,
            "label_and_supervision_provenance": True,
            "graph_ml_task_specifications": True,
            "transductive_and_inductive_learning_modes": True,
            "framework_neutral_graph_ml_model_foundations": True,
            "workspace_graph_ml_runtime_contracts": True,
            "training_evaluation_inference_run_provenance": True,
            "predicted_relationship_envelopes": True,
            "supporting_and_contradicting_evidence_refs": True,
            "deterministic_object_fingerprints": True,
        },
        "roadmap_integration": {
            "begins_second_neural_wave": True,
            "follows_v3650_v3690_language_linguistics_block": True,
            "prepares_v3710_graph_embedding_objects_runtime_contracts": True,
            "prepares_v3720_node_edge_classification_objects": True,
            "prepares_v3730_link_prediction_candidate_relationship_objects": True,
            "prepares_v3740_graph_anomaly_detection": True,
            "prepares_v3750_knowledge_graph_representation_learning": True,
            "prepares_v3760_evidence_graph_neural_analysis_validation_workflow": True,
        },
        "boundaries": {
            "core_trains_graph_models": False,
            "core_runs_graph_inference": False,
            "core_computes_graph_embeddings": False,
            "core_installs_graph_ml_frameworks": False,
            "core_mutates_evidence_graph_from_prediction": False,
            "core_promotes_prediction_to_evidence_edge": False,
            "core_treats_candidate_relationship_as_fact": False,
            "core_certifies_graph_model_quality": False,
            "runtime_may_mutate_evidence_graph": False,
        },
        "reference": {
            "snapshot_count": len(ref.snapshots),
            "evidence_edge_count": sum(len(x.evidence_edges) for x in ref.snapshots),
            "task_count": len(ref.tasks),
            "runtime_contract_count": len(ref.runtime_contracts),
            "run_count": len(ref.run_provenance),
            "predicted_relationship_count": len(ref.predicted_relationships),
            "bundle_fingerprint_sha256": ref.fingerprint(),
            "reference_fixture_is_synthetic": True,
        },
    }
