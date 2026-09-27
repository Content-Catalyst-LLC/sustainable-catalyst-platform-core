from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256

CORE_RELEASE = "3.57.0"
CONTRACT_VERSION = "sc.core.machine-learning-neural-model-object.v1"


class MLTaskKind(str, Enum):
    regression = "regression"
    classification = "classification"
    multiclass_classification = "multiclass-classification"
    multilabel_classification = "multilabel-classification"
    clustering = "clustering"
    anomaly_detection = "anomaly-detection"
    forecasting = "forecasting"
    ranking = "ranking"
    dimensionality_reduction = "dimensionality-reduction"
    representation_learning = "representation-learning"


class LearningParadigm(str, Enum):
    supervised = "supervised"
    unsupervised = "unsupervised"
    semi_supervised = "semi-supervised"
    self_supervised = "self-supervised"
    reinforcement = "reinforcement"
    hybrid = "hybrid"


class MLModelFamily(str, Enum):
    linear = "linear"
    tree_ensemble = "tree-ensemble"
    kernel = "kernel"
    nearest_neighbor = "nearest-neighbor"
    probabilistic = "probabilistic"
    neural_network = "neural-network"
    graph_neural_network = "graph-neural-network"
    transformer = "transformer"
    ensemble = "ensemble"
    hybrid = "hybrid"
    other = "other"


class NeuralArchitectureKind(str, Enum):
    mlp = "mlp"
    cnn = "cnn"
    rnn = "rnn"
    lstm = "lstm"
    gru = "gru"
    transformer = "transformer"
    graph_neural_network = "graph-neural-network"
    autoencoder = "autoencoder"
    variational_autoencoder = "variational-autoencoder"
    diffusion = "diffusion"
    hybrid = "hybrid"
    other = "other"


class FeatureDataType(str, Enum):
    floating = "float"
    integer = "integer"
    boolean = "boolean"
    string = "string"
    categorical = "categorical"
    datetime = "datetime"
    embedding = "embedding"
    tensor = "tensor"


class ExecutionHost(str, Enum):
    workspace = "workspace"
    lab = "lab"
    external = "external"


class MLFeatureSpec(BaseModel):
    name: str = Field(min_length=1, max_length=240)
    data_type: FeatureDataType
    role: Literal["input", "target", "weight", "group", "time", "identifier"] = "input"
    shape: list[int] = Field(default_factory=list)
    nullable: bool = False
    unit: str | None = Field(default=None, max_length=120)
    category_labels: list[str] = Field(default_factory=list)
    transformation_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape_and_categories(self):
        if any(dim < 1 for dim in self.shape):
            raise ValueError("feature shape dimensions must be positive")
        if len(self.category_labels) != len(set(self.category_labels)):
            raise ValueError("category labels must be unique")
        return self


class MLFeatureSchema(BaseModel):
    schema_id: str = Field(min_length=2, max_length=300)
    features: list[MLFeatureSpec] = Field(min_length=1)
    target_names: list[str] = Field(default_factory=list)
    source_dataset_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_schema(self):
        names = [feature.name for feature in self.features]
        if len(names) != len(set(names)):
            raise ValueError("feature names must be unique")
        missing = [name for name in self.target_names if name not in names]
        if missing:
            raise ValueError(f"target_names not present in features: {missing}")
        roles = {feature.name: feature.role for feature in self.features}
        bad = [name for name in self.target_names if roles.get(name) != "target"]
        if bad:
            raise ValueError(f"target_names must reference target-role features: {bad}")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class NeuralLayerSpec(BaseModel):
    layer_id: str = Field(min_length=1, max_length=240)
    layer_kind: str = Field(min_length=1, max_length=240)
    input_refs: list[str] = Field(default_factory=list)
    activation: str | None = Field(default=None, max_length=120)
    output_shape: list[int] = Field(default_factory=list)
    parameter_count: int | None = Field(default=None, ge=0)
    config: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_layer(self):
        if self.layer_id in self.input_refs:
            raise ValueError("neural layer cannot reference itself as an input")
        if len(self.input_refs) != len(set(self.input_refs)):
            raise ValueError("neural layer input_refs must be unique")
        if any(dim < 1 for dim in self.output_shape):
            raise ValueError("layer output shape dimensions must be positive")
        return self


class NeuralArchitectureSpec(BaseModel):
    architecture_id: str = Field(min_length=2, max_length=300)
    architecture_kind: NeuralArchitectureKind
    layers: list[NeuralLayerSpec] = Field(default_factory=list)
    parameter_count: int | None = Field(default=None, ge=0)
    framework_hint: str | None = Field(default=None, max_length=240)
    architecture_artifact_ref: str | None = Field(default=None, max_length=1000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_architecture(self):
        ids = [layer.layer_id for layer in self.layers]
        if len(ids) != len(set(ids)):
            raise ValueError("neural layer ids must be unique")
        seen: set[str] = set()
        for layer in self.layers:
            invalid = [
                ref for ref in layer.input_refs
                if not ref.startswith("input:") and ref not in seen
            ]
            if invalid:
                raise ValueError(
                    "neural layer input refs must point to declared inputs or earlier layers: "
                    f"{invalid}"
                )
            seen.add(layer.layer_id)
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MLObjectiveSpec(BaseModel):
    objective_id: str = Field(min_length=2, max_length=300)
    task: MLTaskKind
    learning_paradigm: LearningParadigm
    loss_name: str | None = Field(default=None, max_length=240)
    metric_names: list[str] = Field(default_factory=list)
    optimization_direction: Literal["minimize", "maximize", "descriptive"] = "descriptive"
    class_labels: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_objective(self):
        if len(self.metric_names) != len(set(self.metric_names)):
            raise ValueError("metric names must be unique")
        if len(self.class_labels) != len(set(self.class_labels)):
            raise ValueError("class labels must be unique")
        return self


class MLRuntimeBinding(BaseModel):
    runtime_binding_id: str = Field(min_length=2, max_length=300)
    adapter_id: str = Field(min_length=2, max_length=300)
    runtime_id: str = Field(min_length=2, max_length=300)
    execution_host: ExecutionHost
    framework: str | None = Field(default=None, max_length=240)
    framework_version: str | None = Field(default=None, max_length=120)
    accelerator: str | None = Field(default=None, max_length=120)
    environment_ref: str | None = Field(default=None, max_length=500)
    supported_operations: list[Literal["train", "evaluate", "infer", "embed", "export"]] = Field(default_factory=list)
    arbitrary_code_allowed: Literal[False] = False
    package_install_allowed: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_operations(self):
        if len(self.supported_operations) != len(set(self.supported_operations)):
            raise ValueError("supported operations must be unique")
        return self


class MLModelSpecification(BaseModel):
    model_spec_id: str = Field(min_length=2, max_length=300)
    ai_model_ref: str = Field(min_length=2, max_length=500)
    ai_model_version_ref: str | None = Field(default=None, max_length=500)
    model_family: MLModelFamily
    algorithm_name: str = Field(min_length=1, max_length=300)
    feature_schema: MLFeatureSchema
    objective: MLObjectiveSpec
    neural_architecture: NeuralArchitectureSpec | None = None
    hyperparameters: dict[str, Any] = Field(default_factory=dict)
    runtime_bindings: list[MLRuntimeBinding] = Field(default_factory=list)
    research_model_ref: str | None = Field(default=None, max_length=500)
    predictive_model_ref: str | None = Field(default=None, max_length=500)
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_model_specification(self):
        neural_families = {MLModelFamily.neural_network, MLModelFamily.graph_neural_network, MLModelFamily.transformer}
        if self.model_family in neural_families and self.neural_architecture is None:
            raise ValueError("neural model families require a neural_architecture")
        ids = [binding.runtime_binding_id for binding in self.runtime_bindings]
        if len(ids) != len(set(ids)):
            raise ValueError("runtime binding ids must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MLDataSplitSpec(BaseModel):
    strategy: Literal["holdout", "k-fold", "time-series", "grouped", "external"]
    train_fraction: float | None = Field(default=None, gt=0, lt=1)
    validation_fraction: float | None = Field(default=None, gt=0, lt=1)
    test_fraction: float | None = Field(default=None, gt=0, lt=1)
    folds: int | None = Field(default=None, ge=2, le=1000)
    group_feature: str | None = Field(default=None, max_length=240)
    time_feature: str | None = Field(default=None, max_length=240)

    @model_validator(mode="after")
    def validate_split(self):
        fractions = [x for x in (self.train_fraction, self.validation_fraction, self.test_fraction) if x is not None]
        if fractions and sum(fractions) > 1.0000001:
            raise ValueError("data split fractions cannot sum to more than 1")
        if self.strategy == "k-fold" and self.folds is None:
            raise ValueError("k-fold split requires folds")
        if self.strategy == "grouped" and not self.group_feature:
            raise ValueError("grouped split requires group_feature")
        if self.strategy == "time-series" and not self.time_feature:
            raise ValueError("time-series split requires time_feature")
        return self


class MLTrainingPlan(BaseModel):
    training_plan_id: str = Field(min_length=2, max_length=300)
    model_spec_ref: str = Field(min_length=2, max_length=500)
    dataset_version_refs: list[str] = Field(min_length=1)
    validation_dataset_refs: list[str] = Field(default_factory=list)
    split: MLDataSplitSpec
    random_seed: int | None = None
    runtime_binding_ref: str = Field(min_length=2, max_length=300)
    environment_ref: str | None = Field(default=None, max_length=500)
    computational_job_ref: str | None = Field(default=None, max_length=500)
    output_artifact_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_training_plan(self):
        if len(self.dataset_version_refs) != len(set(self.dataset_version_refs)):
            raise ValueError("dataset_version_refs must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MLInferencePlan(BaseModel):
    inference_plan_id: str = Field(min_length=2, max_length=300)
    model_spec_ref: str = Field(min_length=2, max_length=500)
    model_version_ref: str = Field(min_length=2, max_length=500)
    input_schema_ref: str = Field(min_length=2, max_length=500)
    runtime_binding_ref: str = Field(min_length=2, max_length=300)
    computational_job_ref: str | None = Field(default=None, max_length=500)
    batch_size: int | None = Field(default=None, ge=1)
    deterministic_requested: bool | None = None
    output_artifact_kind: str | None = Field(default=None, max_length=240)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MLModelBundle(BaseModel):
    model_spec: MLModelSpecification
    training_plan: MLTrainingPlan | None = None
    inference_plan: MLInferencePlan | None = None

    @model_validator(mode="after")
    def validate_bundle(self):
        spec_ref = self.model_spec.model_spec_id
        runtime_ids = {item.runtime_binding_id for item in self.model_spec.runtime_bindings}
        if self.training_plan:
            if self.training_plan.model_spec_ref != spec_ref:
                raise ValueError("training plan model_spec_ref must match model specification")
            if self.training_plan.runtime_binding_ref not in runtime_ids:
                raise ValueError("training plan runtime_binding_ref is not declared by model specification")
        if self.inference_plan:
            if self.inference_plan.model_spec_ref != spec_ref:
                raise ValueError("inference plan model_spec_ref must match model specification")
            if self.inference_plan.runtime_binding_ref not in runtime_ids:
                raise ValueError("inference plan runtime_binding_ref is not declared by model specification")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


def reference_ml_model_bundle() -> MLModelBundle:
    feature_schema = MLFeatureSchema(
        schema_id="ml-feature-schema:reference-tabular-regression:v1",
        features=[
            MLFeatureSpec(name="temperature_c", data_type=FeatureDataType.floating, role="input", unit="degC"),
            MLFeatureSpec(name="humidity_pct", data_type=FeatureDataType.floating, role="input", unit="percent"),
            MLFeatureSpec(name="energy_kwh", data_type=FeatureDataType.floating, role="target", unit="kWh"),
        ],
        target_names=["energy_kwh"],
        source_dataset_refs=["dataset-version:reference-energy:v1"],
    )
    architecture = NeuralArchitectureSpec(
        architecture_id="neural-architecture:reference-energy-mlp:v1",
        architecture_kind=NeuralArchitectureKind.mlp,
        layers=[
            NeuralLayerSpec(layer_id="dense-1", layer_kind="dense", input_refs=["input:features"], activation="relu", output_shape=[32], parameter_count=96),
            NeuralLayerSpec(layer_id="output", layer_kind="dense", input_refs=["dense-1"], activation="linear", output_shape=[1], parameter_count=33),
        ],
        parameter_count=129,
        framework_hint="python-ml-runtime",
    )
    objective = MLObjectiveSpec(
        objective_id="ml-objective:reference-energy-regression:v1",
        task=MLTaskKind.regression,
        learning_paradigm=LearningParadigm.supervised,
        loss_name="mean-squared-error",
        metric_names=["mae", "rmse"],
        optimization_direction="minimize",
    )
    runtime = MLRuntimeBinding(
        runtime_binding_id="ml-runtime-binding:reference-python:v1",
        adapter_id="adapter:sc-runtime-python",
        runtime_id="sc-runtime-python",
        execution_host=ExecutionHost.workspace,
        framework="external-ml-framework",
        environment_ref="environment:reference-ml-python",
        supported_operations=["train", "evaluate", "infer", "export"],
    )
    spec = MLModelSpecification(
        model_spec_id="ml-model-spec:reference-energy-neural-regressor:v1",
        ai_model_ref="ai-model:reference-scientific-regressor",
        ai_model_version_ref="ai-model-version:reference-scientific-regressor:1.0.0",
        model_family=MLModelFamily.neural_network,
        algorithm_name="multilayer-perceptron",
        feature_schema=feature_schema,
        objective=objective,
        neural_architecture=architecture,
        hyperparameters={"epochs": 100, "batch_size": 32, "learning_rate": 0.001},
        runtime_bindings=[runtime],
        research_model_ref="research-model:reference-energy-regressor",
        predictive_model_ref="predictive-model:reference-energy-regressor",
        provenance={"purpose": "Platform Core v3.57.0 ML/neural object contract proof"},
    )
    training = MLTrainingPlan(
        training_plan_id="ml-training-plan:reference-energy:v1",
        model_spec_ref=spec.model_spec_id,
        dataset_version_refs=["dataset-version:reference-energy:v1"],
        split=MLDataSplitSpec(strategy="holdout", train_fraction=0.8, validation_fraction=0.1, test_fraction=0.1),
        random_seed=570,
        runtime_binding_ref=runtime.runtime_binding_id,
        environment_ref=runtime.environment_ref,
    )
    inference = MLInferencePlan(
        inference_plan_id="ml-inference-plan:reference-energy:v1",
        model_spec_ref=spec.model_spec_id,
        model_version_ref=spec.ai_model_version_ref or "ai-model-version:reference-scientific-regressor:1.0.0",
        input_schema_ref=feature_schema.schema_id,
        runtime_binding_ref=runtime.runtime_binding_id,
        batch_size=64,
        deterministic_requested=True,
        output_artifact_kind="prediction-table",
    )
    return MLModelBundle(model_spec=spec, training_plan=training, inference_plan=inference)


def contract_document() -> dict[str, Any]:
    reference = reference_ml_model_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "object_types": [
            "MLFeatureSpec", "MLFeatureSchema", "NeuralLayerSpec", "NeuralArchitectureSpec",
            "MLObjectiveSpec", "MLRuntimeBinding", "MLModelSpecification", "MLDataSplitSpec",
            "MLTrainingPlan", "MLInferencePlan", "MLModelBundle",
        ],
        "model_families": [item.value for item in MLModelFamily],
        "neural_architectures": [item.value for item in NeuralArchitectureKind],
        "integration": {
            "extends_ai_model_object_system_v3270": True,
            "reuses_ai_model_identity_and_version_refs": True,
            "reuses_dataset_version_lineage": True,
            "reuses_computational_job_contract": True,
            "reuses_runtime_adapter_registry": True,
            "reuses_execution_environment_provenance": True,
            "workspace_is_default_compute_host": True,
            "lab_is_supported_experiment_host": True,
            "core_defines_workspace_computes_lab_experiments_products_consume": True,
        },
        "deep_learning_readiness": {
            "neural_architecture_objects": True,
            "layer_graph_objects": True,
            "tensor_feature_shapes": True,
            "training_and_inference_plan_objects": True,
            "framework_neutral_runtime_bindings": True,
            "future_accelerator_bindings_supported": True,
        },
        "boundaries": {
            "core_trains_models": False,
            "core_runs_inference": False,
            "core_installs_ml_packages": False,
            "core_accepts_arbitrary_executable_model_code": False,
            "core_selects_models_autonomously": False,
            "core_ranks_models": False,
            "core_certifies_model_quality": False,
            "core_claims_prediction_truth": False,
            "runtime_execution_external_to_core": True,
        },
        "reference": {
            "model_spec_id": reference.model_spec.model_spec_id,
            "feature_schema_id": reference.model_spec.feature_schema.schema_id,
            "training_plan_id": reference.training_plan.training_plan_id if reference.training_plan else None,
            "inference_plan_id": reference.inference_plan.inference_plan_id if reference.inference_plan else None,
            "bundle_fingerprint_sha256": reference.fingerprint(),
        },
    }
