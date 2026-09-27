from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .machine_learning_models import MLModelSpecification, MLTrainingPlan
from .ml_training_lineage import MLCodeReference, MLSeedState, reference_training_lineage_bundle

CORE_RELEASE = "3.59.0"
CONTRACT_VERSION = "sc.core.neural-dataset-feature-transformation-provenance.v1"


class MLRawSourceKind(str, Enum):
    file = "file"
    database = "database"
    api = "api"
    sensor = "sensor"
    repository = "repository"
    publication = "publication"
    object_store = "object-store"
    derived = "derived"
    other = "other"


class MLPartitionRole(str, Enum):
    train = "train"
    validation = "validation"
    test = "test"
    inference = "inference"
    external = "external"
    custom = "custom"


class MLTransformationKind(str, Enum):
    identity = "identity"
    cast = "cast"
    normalize = "normalize"
    standardize = "standardize"
    impute = "impute"
    encode = "encode"
    tokenize = "tokenize"
    resize = "resize"
    crop = "crop"
    aggregate = "aggregate"
    window = "window"
    derive = "derive"
    filter = "filter"
    project = "project"
    feature_extract = "feature-extract"
    other_declarative = "other-declarative"


class MLRepresentationKind(str, Enum):
    tabular = "tabular"
    sequence = "sequence"
    image = "image"
    graph = "graph"
    text = "text"
    multimodal = "multimodal"
    tensor = "tensor"
    other = "other"


class MLTensorDType(str, Enum):
    float16 = "float16"
    float32 = "float32"
    float64 = "float64"
    int8 = "int8"
    int16 = "int16"
    int32 = "int32"
    int64 = "int64"
    bool = "bool"


class MLTensorLayout(str, Enum):
    tabular = "tabular"
    batch_first = "batch-first"
    channels_first = "channels-first"
    channels_last = "channels-last"
    sequence = "sequence"
    graph = "graph"
    custom = "custom"


class MLRawSourceReference(BaseModel):
    source_id: str = Field(min_length=2, max_length=300)
    source_kind: MLRawSourceKind
    source_ref: str = Field(min_length=2, max_length=1500)
    source_version: str | None = Field(default=None, max_length=300)
    content_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    retrieved_at: str | None = Field(default=None, max_length=80)
    license_ref: str | None = Field(default=None, max_length=500)
    evidence_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_source(self):
        if len(self.evidence_refs) != len(set(self.evidence_refs)):
            raise ValueError("raw-source evidence_refs must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MLDatasetSnapshotRecord(BaseModel):
    snapshot_id: str = Field(min_length=2, max_length=300)
    dataset_version_ref: str = Field(min_length=2, max_length=500)
    raw_source_refs: list[str] = Field(min_length=1)
    feature_schema_ref: str = Field(min_length=2, max_length=500)
    storage_artifact_ref: str = Field(min_length=2, max_length=1000)
    content_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    record_count: int | None = Field(default=None, ge=0)
    materialization_job_ref: str | None = Field(default=None, max_length=500)
    created_at: str | None = Field(default=None, max_length=80)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_snapshot(self):
        if len(self.raw_source_refs) != len(set(self.raw_source_refs)):
            raise ValueError("snapshot raw_source_refs must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MLDatasetPartitionRecord(BaseModel):
    partition_id: str = Field(min_length=2, max_length=300)
    dataset_version_ref: str = Field(min_length=2, max_length=500)
    snapshot_ref: str = Field(min_length=2, max_length=500)
    role: MLPartitionRole
    selection_method: Literal["deterministic-index", "random-seeded", "time-window", "group-key", "external", "custom-declarative"]
    selection_parameters: dict[str, Any] = Field(default_factory=dict)
    sample_count: int | None = Field(default=None, ge=0)
    index_artifact_ref: str | None = Field(default=None, max_length=1000)
    index_artifact_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    random_seed: int | None = None
    executable_selector_embedded: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_partition(self):
        if self.selection_method == "random-seeded" and self.random_seed is None:
            raise ValueError("random-seeded partition requires random_seed")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MLTransformationStepRecord(BaseModel):
    transformation_id: str = Field(min_length=2, max_length=300)
    ordinal: int = Field(ge=1)
    operation_kind: MLTransformationKind
    input_feature_refs: list[str] = Field(default_factory=list)
    output_feature_refs: list[str] = Field(min_length=1)
    parameters: dict[str, Any] = Field(default_factory=dict)
    fitted_on_partition_ref: str | None = Field(default=None, max_length=500)
    fitted_state_artifact_ref: str | None = Field(default=None, max_length=1000)
    fitted_state_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    implementation_ref: str | None = Field(default=None, max_length=1000)
    implementation_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    deterministic: bool = True
    arbitrary_executable_payload_embedded: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_step(self):
        if len(self.input_feature_refs) != len(set(self.input_feature_refs)):
            raise ValueError("transformation input_feature_refs must be unique")
        if len(self.output_feature_refs) != len(set(self.output_feature_refs)):
            raise ValueError("transformation output_feature_refs must be unique")
        return self


class MLTransformationPipelineRecord(BaseModel):
    pipeline_id: str = Field(min_length=2, max_length=300)
    dataset_version_ref: str = Field(min_length=2, max_length=500)
    source_partition_ref: str = Field(min_length=2, max_length=500)
    feature_schema_ref: str = Field(min_length=2, max_length=500)
    steps: list[MLTransformationStepRecord] = Field(min_length=1)
    runtime_binding_ref: str | None = Field(default=None, max_length=500)
    environment_ref: str | None = Field(default=None, max_length=500)
    computational_job_ref: str | None = Field(default=None, max_length=500)
    code_reference: MLCodeReference | None = None
    seed_state: MLSeedState | None = None
    output_representation_ref: str = Field(min_length=2, max_length=500)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_pipeline(self):
        ids = [step.transformation_id for step in self.steps]
        ordinals = [step.ordinal for step in self.steps]
        if len(ids) != len(set(ids)):
            raise ValueError("transformation ids must be unique within pipeline")
        if len(ordinals) != len(set(ordinals)):
            raise ValueError("transformation ordinals must be unique")
        if sorted(ordinals) != list(range(1, len(ordinals) + 1)):
            raise ValueError("transformation ordinals must be contiguous starting at 1")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MLFeatureRepresentationRecord(BaseModel):
    representation_id: str = Field(min_length=2, max_length=300)
    dataset_version_ref: str = Field(min_length=2, max_length=500)
    partition_ref: str = Field(min_length=2, max_length=500)
    feature_schema_ref: str = Field(min_length=2, max_length=500)
    transformation_pipeline_ref: str = Field(min_length=2, max_length=500)
    representation_kind: MLRepresentationKind
    feature_names: list[str] = Field(min_length=1)
    target_names: list[str] = Field(default_factory=list)
    shape: list[int] = Field(default_factory=list)
    artifact_ref: str = Field(min_length=2, max_length=1000)
    artifact_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    sample_count: int | None = Field(default=None, ge=0)
    created_at: str | None = Field(default=None, max_length=80)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_representation(self):
        if len(self.feature_names) != len(set(self.feature_names)):
            raise ValueError("representation feature_names must be unique")
        if len(self.target_names) != len(set(self.target_names)):
            raise ValueError("representation target_names must be unique")
        missing = [name for name in self.target_names if name not in self.feature_names]
        if missing:
            raise ValueError(f"representation target_names must exist in feature_names: {missing}")
        if any(dim < 1 for dim in self.shape):
            raise ValueError("representation shape dimensions must be positive")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MLTensorInputRecord(BaseModel):
    tensor_input_id: str = Field(min_length=2, max_length=300)
    representation_ref: str = Field(min_length=2, max_length=500)
    model_spec_ref: str = Field(min_length=2, max_length=500)
    training_plan_ref: str | None = Field(default=None, max_length=500)
    input_name: str = Field(min_length=1, max_length=240)
    dtype: MLTensorDType
    layout: MLTensorLayout
    shape: list[int] = Field(min_length=1)
    feature_names: list[str] = Field(min_length=1)
    artifact_ref: str = Field(min_length=2, max_length=1000)
    artifact_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    batch_axis: int | None = Field(default=0, ge=0)
    created_at: str | None = Field(default=None, max_length=80)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_tensor(self):
        if any(dim < 1 for dim in self.shape):
            raise ValueError("tensor shape dimensions must be positive")
        if len(self.feature_names) != len(set(self.feature_names)):
            raise ValueError("tensor feature_names must be unique")
        if self.batch_axis is not None and self.batch_axis >= len(self.shape):
            raise ValueError("batch_axis must resolve within tensor shape")
        if self.layout == MLTensorLayout.tabular and self.shape[-1] != len(self.feature_names):
            raise ValueError("tabular tensor final dimension must equal number of feature_names")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MLDatasetFeatureTransformationLineageBundle(BaseModel):
    model_spec: MLModelSpecification
    training_plan: MLTrainingPlan
    raw_sources: list[MLRawSourceReference] = Field(min_length=1)
    dataset_snapshots: list[MLDatasetSnapshotRecord] = Field(min_length=1)
    partitions: list[MLDatasetPartitionRecord] = Field(min_length=1)
    transformation_pipelines: list[MLTransformationPipelineRecord] = Field(min_length=1)
    feature_representations: list[MLFeatureRepresentationRecord] = Field(min_length=1)
    tensor_inputs: list[MLTensorInputRecord] = Field(min_length=1)
    training_experiment_refs: list[str] = Field(default_factory=list)
    training_run_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_bundle(self):
        if self.training_plan.model_spec_ref != self.model_spec.model_spec_id:
            raise ValueError("training plan must reference bundled model specification")

        source_ids = [x.source_id for x in self.raw_sources]
        snapshot_ids = [x.snapshot_id for x in self.dataset_snapshots]
        partition_ids = [x.partition_id for x in self.partitions]
        pipeline_ids = [x.pipeline_id for x in self.transformation_pipelines]
        representation_ids = [x.representation_id for x in self.feature_representations]
        tensor_ids = [x.tensor_input_id for x in self.tensor_inputs]
        for label, values in (
            ("raw source", source_ids), ("dataset snapshot", snapshot_ids), ("partition", partition_ids),
            ("transformation pipeline", pipeline_ids), ("feature representation", representation_ids),
            ("tensor input", tensor_ids),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{label} ids must be unique")

        source_set = set(source_ids)
        snapshot_by_id = {x.snapshot_id: x for x in self.dataset_snapshots}
        partition_by_id = {x.partition_id: x for x in self.partitions}
        pipeline_by_id = {x.pipeline_id: x for x in self.transformation_pipelines}
        representation_by_id = {x.representation_id: x for x in self.feature_representations}
        schema_ref = self.model_spec.feature_schema.schema_id
        schema_names = [f.name for f in self.model_spec.feature_schema.features]
        input_names = [f.name for f in self.model_spec.feature_schema.features if f.role == "input"]
        target_names = list(self.model_spec.feature_schema.target_names)

        required_datasets = set(self.training_plan.dataset_version_refs) | set(self.training_plan.validation_dataset_refs)
        snapshot_datasets = {x.dataset_version_ref for x in self.dataset_snapshots}
        missing_datasets = required_datasets - snapshot_datasets
        if missing_datasets:
            raise ValueError(f"training-plan dataset versions missing dataset snapshots: {sorted(missing_datasets)}")

        for snapshot in self.dataset_snapshots:
            unknown = set(snapshot.raw_source_refs) - source_set
            if unknown:
                raise ValueError(f"snapshot references unknown raw sources: {sorted(unknown)}")
            if snapshot.feature_schema_ref != schema_ref:
                raise ValueError("dataset snapshot feature_schema_ref must match model feature schema")

        for partition in self.partitions:
            snapshot = snapshot_by_id.get(partition.snapshot_ref)
            if snapshot is None:
                raise ValueError("partition snapshot_ref must resolve within bundle")
            if partition.dataset_version_ref != snapshot.dataset_version_ref:
                raise ValueError("partition dataset_version_ref must match referenced snapshot")

        for pipeline in self.transformation_pipelines:
            partition = partition_by_id.get(pipeline.source_partition_ref)
            if partition is None:
                raise ValueError("transformation pipeline source_partition_ref must resolve within bundle")
            if pipeline.dataset_version_ref != partition.dataset_version_ref:
                raise ValueError("pipeline dataset_version_ref must match source partition")
            if pipeline.feature_schema_ref != schema_ref:
                raise ValueError("pipeline feature_schema_ref must match model feature schema")
            if pipeline.output_representation_ref not in representation_by_id:
                raise ValueError("pipeline output_representation_ref must resolve within bundle")
            for step in pipeline.steps:
                if step.fitted_on_partition_ref:
                    fitted = partition_by_id.get(step.fitted_on_partition_ref)
                    if fitted is None:
                        raise ValueError("fitted_on_partition_ref must resolve within bundle")
                    if fitted.role != MLPartitionRole.train:
                        raise ValueError("fitted transformation state must be fitted on a training partition")

        for representation in self.feature_representations:
            partition = partition_by_id.get(representation.partition_ref)
            if partition is None:
                raise ValueError("representation partition_ref must resolve within bundle")
            if representation.dataset_version_ref != partition.dataset_version_ref:
                raise ValueError("representation dataset_version_ref must match partition")
            if representation.feature_schema_ref != schema_ref:
                raise ValueError("representation feature_schema_ref must match model feature schema")
            pipeline = pipeline_by_id.get(representation.transformation_pipeline_ref)
            if pipeline is None:
                raise ValueError("representation transformation_pipeline_ref must resolve within bundle")
            if pipeline.output_representation_ref != representation.representation_id:
                raise ValueError("pipeline output_representation_ref must match representation")
            if set(representation.feature_names) != set(schema_names):
                raise ValueError("representation feature_names must exactly match model feature schema")
            if set(representation.target_names) != set(target_names):
                raise ValueError("representation target_names must match model feature schema targets")

        for tensor in self.tensor_inputs:
            representation = representation_by_id.get(tensor.representation_ref)
            if representation is None:
                raise ValueError("tensor representation_ref must resolve within bundle")
            if tensor.model_spec_ref != self.model_spec.model_spec_id:
                raise ValueError("tensor model_spec_ref must match bundled model specification")
            if tensor.training_plan_ref and tensor.training_plan_ref != self.training_plan.training_plan_id:
                raise ValueError("tensor training_plan_ref must match bundled training plan")
            if tensor.feature_names != input_names:
                raise ValueError("tensor feature_names must match ordered input-role features in model feature schema")

        if len(self.training_experiment_refs) != len(set(self.training_experiment_refs)):
            raise ValueError("training_experiment_refs must be unique")
        if len(self.training_run_refs) != len(set(self.training_run_refs)):
            raise ValueError("training_run_refs must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


def reference_dataset_feature_transformation_bundle() -> MLDatasetFeatureTransformationLineageBundle:
    training = reference_training_lineage_bundle()
    spec = training.model_spec
    plan = training.training_plan
    dataset_ref = plan.dataset_version_refs[0]
    schema_ref = spec.feature_schema.schema_id
    train_partition = "ml-partition:reference-energy:train"
    validation_partition = "ml-partition:reference-energy:validation"
    test_partition = "ml-partition:reference-energy:test"

    raw_sources = [
        MLRawSourceReference(source_id="ml-source:reference-energy:weather", source_kind=MLRawSourceKind.api, source_ref="source:reference-weather-observations", source_version="v1", content_sha256="4"*64, retrieved_at="2026-09-27T00:00:00Z"),
        MLRawSourceReference(source_id="ml-source:reference-energy:meter", source_kind=MLRawSourceKind.sensor, source_ref="source:reference-energy-meter", source_version="v1", content_sha256="5"*64, retrieved_at="2026-09-27T00:00:00Z"),
    ]
    snapshot = MLDatasetSnapshotRecord(snapshot_id="ml-dataset-snapshot:reference-energy:v1", dataset_version_ref=dataset_ref, raw_source_refs=[x.source_id for x in raw_sources], feature_schema_ref=schema_ref, storage_artifact_ref="artifact:reference-energy:dataset-v1", content_sha256="6"*64, record_count=1000, materialization_job_ref="computational-job:reference-energy-materialize:001", created_at="2026-09-27T00:01:00Z")
    partitions = [
        MLDatasetPartitionRecord(partition_id=train_partition, dataset_version_ref=dataset_ref, snapshot_ref=snapshot.snapshot_id, role=MLPartitionRole.train, selection_method="random-seeded", selection_parameters={"fraction":0.8}, sample_count=800, index_artifact_ref="artifact:reference-energy:train-index", index_artifact_sha256="7"*64, random_seed=570),
        MLDatasetPartitionRecord(partition_id=validation_partition, dataset_version_ref=dataset_ref, snapshot_ref=snapshot.snapshot_id, role=MLPartitionRole.validation, selection_method="random-seeded", selection_parameters={"fraction":0.1}, sample_count=100, index_artifact_ref="artifact:reference-energy:validation-index", index_artifact_sha256="8"*64, random_seed=570),
        MLDatasetPartitionRecord(partition_id=test_partition, dataset_version_ref=dataset_ref, snapshot_ref=snapshot.snapshot_id, role=MLPartitionRole.test, selection_method="random-seeded", selection_parameters={"fraction":0.1}, sample_count=100, index_artifact_ref="artifact:reference-energy:test-index", index_artifact_sha256="9"*64, random_seed=570),
    ]
    code_ref = MLCodeReference(source_ref="repository:sustainable-catalyst/reference-ml-data-pipeline", revision="reference-data-revision-001", content_sha256="a"*64)
    seed = MLSeedState(primary_seed=570, framework_seeds={"python":570,"numpy":570}, deterministic_requested=True)

    reps = []
    pipes = []
    tensors = []
    for role, partition_id, count, suffix, hash_char in [
        ("train", train_partition, 800, "train", "b"),
        ("validation", validation_partition, 100, "validation", "c"),
        ("test", test_partition, 100, "test", "d"),
    ]:
        rep_id = f"ml-feature-representation:reference-energy:{suffix}"
        pipeline_id = f"ml-transform-pipeline:reference-energy:{suffix}"
        steps = [
            MLTransformationStepRecord(transformation_id=f"ml-transform:reference-energy:{suffix}:standardize-inputs", ordinal=1, operation_kind=MLTransformationKind.standardize, input_feature_refs=["temperature_c","humidity_pct"], output_feature_refs=["temperature_c","humidity_pct"], parameters={"method":"z-score"}, fitted_on_partition_ref=train_partition, fitted_state_artifact_ref="artifact:reference-energy:standardization-state", fitted_state_sha256="e"*64, implementation_ref="implementation:reference-standardization:v1", implementation_sha256="f"*64),
            MLTransformationStepRecord(transformation_id=f"ml-transform:reference-energy:{suffix}:target-identity", ordinal=2, operation_kind=MLTransformationKind.identity, input_feature_refs=["energy_kwh"], output_feature_refs=["energy_kwh"], implementation_ref="implementation:reference-target-identity:v1", implementation_sha256="1"*64),
        ]
        pipes.append(MLTransformationPipelineRecord(pipeline_id=pipeline_id, dataset_version_ref=dataset_ref, source_partition_ref=partition_id, feature_schema_ref=schema_ref, steps=steps, runtime_binding_ref=plan.runtime_binding_ref, environment_ref=plan.environment_ref, computational_job_ref=f"computational-job:reference-energy-transform:{suffix}", code_reference=code_ref, seed_state=seed, output_representation_ref=rep_id))
        reps.append(MLFeatureRepresentationRecord(representation_id=rep_id, dataset_version_ref=dataset_ref, partition_ref=partition_id, feature_schema_ref=schema_ref, transformation_pipeline_ref=pipeline_id, representation_kind=MLRepresentationKind.tabular, feature_names=["temperature_c","humidity_pct","energy_kwh"], target_names=["energy_kwh"], shape=[count,3], artifact_ref=f"artifact:reference-energy:features-{suffix}", artifact_sha256=hash_char*64, sample_count=count, created_at="2026-09-27T00:05:00Z"))
        tensors.append(MLTensorInputRecord(tensor_input_id=f"ml-tensor-input:reference-energy:{suffix}", representation_ref=rep_id, model_spec_ref=spec.model_spec_id, training_plan_ref=plan.training_plan_id, input_name="features", dtype=MLTensorDType.float32, layout=MLTensorLayout.tabular, shape=[count,2], feature_names=["temperature_c","humidity_pct"], artifact_ref=f"artifact:reference-energy:tensor-{suffix}", artifact_sha256=("2" if suffix=="train" else "3" if suffix=="validation" else "0")*64, batch_axis=0, created_at="2026-09-27T00:06:00Z"))

    return MLDatasetFeatureTransformationLineageBundle(
        model_spec=spec,
        training_plan=plan,
        raw_sources=raw_sources,
        dataset_snapshots=[snapshot],
        partitions=partitions,
        transformation_pipelines=pipes,
        feature_representations=reps,
        tensor_inputs=tensors,
        training_experiment_refs=[training.experiment.experiment_id],
        training_run_refs=[run.training_run_id for run in training.training_runs],
    )


def contract_document() -> dict[str, Any]:
    ref = reference_dataset_feature_transformation_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "object_types": [
            "MLRawSourceReference", "MLDatasetSnapshotRecord", "MLDatasetPartitionRecord",
            "MLTransformationStepRecord", "MLTransformationPipelineRecord",
            "MLFeatureRepresentationRecord", "MLTensorInputRecord",
            "MLDatasetFeatureTransformationLineageBundle",
        ],
        "lineage_chain": [
            "MLRawSourceReference", "MLDatasetSnapshotRecord", "MLDatasetPartitionRecord",
            "MLTransformationPipelineRecord", "MLFeatureRepresentationRecord", "MLTensorInputRecord",
        ],
        "integration": {
            "extends_machine_learning_neural_model_foundation_v3570": True,
            "extends_training_run_checkpoint_experiment_lineage_v3580": True,
            "binds_model_feature_schema": True,
            "binds_training_plan_dataset_versions": True,
            "links_training_experiments_and_runs": True,
            "reuses_runtime_binding_and_environment_refs": True,
            "workspace_remains_default_compute_host": True,
            "lab_remains_experiment_host": True,
        },
        "reproducibility": {
            "raw_source_content_hashes_supported": True,
            "dataset_snapshot_hashes_supported": True,
            "partition_index_hashes_supported": True,
            "transformation_implementation_hashes_supported": True,
            "fitted_state_hashes_supported": True,
            "feature_representation_hashes_supported": True,
            "tensor_artifact_hashes_supported": True,
            "deterministic_bundle_fingerprint": True,
        },
        "leakage_safeguards": {
            "fitted_transform_partition_must_resolve": True,
            "fitted_transform_state_must_use_training_partition": True,
            "evaluation_partition_fit_is_rejected": True,
        },
        "boundaries": {
            "core_ingests_raw_data": False,
            "core_materializes_datasets": False,
            "core_executes_splits": False,
            "core_applies_transformations": False,
            "core_fits_transform_state": False,
            "core_creates_tensors": False,
            "core_installs_ml_packages": False,
            "core_accepts_arbitrary_executable_transform_payloads": False,
            "core_treats_model_inputs_as_evidence": False,
        },
        "reference": {
            "dataset_version_ref": ref.dataset_snapshots[0].dataset_version_ref,
            "snapshot_id": ref.dataset_snapshots[0].snapshot_id,
            "train_partition_id": next(x.partition_id for x in ref.partitions if x.role == MLPartitionRole.train),
            "tensor_input_id": ref.tensor_inputs[0].tensor_input_id,
            "bundle_fingerprint_sha256": ref.fingerprint(),
        },
    }
