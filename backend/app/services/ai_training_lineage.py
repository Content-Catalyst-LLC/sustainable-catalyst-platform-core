from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256

CORE_RELEASE = "3.28.0"
CONTRACT_VERSION = "sc.core.ai-training-lineage.v1"
AI_MODEL_CONTRACT_VERSION = "sc.core.ai-model.v1"
COMPUTATIONAL_JOB_CONTRACT_VERSION = "sc.core.computational-job.v1"
ENVIRONMENT_PROVENANCE_CONTRACT_VERSION = "sc.core.execution-environment-provenance.v1"


class DatasetRole(str, Enum):
    source = "source"
    training = "training"
    validation = "validation"
    evaluation = "evaluation"
    holdout = "holdout"
    inference = "inference"
    reference = "reference"


class DatasetModality(str, Enum):
    tabular = "tabular"
    text = "text"
    image = "image"
    audio = "audio"
    video = "video"
    geospatial = "geospatial"
    time_series = "time-series"
    graph = "graph"
    multimodal = "multimodal"
    other = "other"


class DatasetIdentity(BaseModel):
    dataset_id: str = Field(min_length=2, max_length=240)
    name: str = Field(min_length=1, max_length=300)
    modality: DatasetModality
    description: str | None = Field(default=None, max_length=10000)
    source_refs: list[str] = Field(default_factory=list)
    knowledge_library_refs: list[str] = Field(default_factory=list)
    external_identifier: str | None = Field(default=None, max_length=1000)
    license_ref: str | None = Field(default=None, max_length=1000)
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class DatasetArtifact(BaseModel):
    artifact_id: str = Field(min_length=2, max_length=240)
    artifact_kind: Literal[
        "data",
        "schema",
        "dictionary",
        "labels",
        "split-index",
        "statistics",
        "manifest",
        "other",
    ]
    uri: str | None = Field(default=None, max_length=4000)
    content_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    size_bytes: int | None = Field(default=None, ge=0)
    media_type: str | None = Field(default=None, max_length=255)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DatasetVersion(BaseModel):
    dataset_version_id: str = Field(min_length=2, max_length=300)
    dataset_id: str = Field(min_length=2, max_length=240)
    version: str = Field(min_length=1, max_length=240)
    row_count: int | None = Field(default=None, ge=0)
    column_count: int | None = Field(default=None, ge=0)
    content_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    schema_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    parent_dataset_version_ref: str | None = Field(default=None, max_length=300)
    runtime_environment_ref: str | None = Field(default=None, max_length=300)
    creation_job_ref: str | None = Field(default=None, max_length=300)
    artifacts: list[DatasetArtifact] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_version(self):
        if self.parent_dataset_version_ref == self.dataset_version_id:
            raise ValueError("parent_dataset_version_ref cannot reference itself")
        artifact_ids = [item.artifact_id for item in self.artifacts]
        if len(artifact_ids) != len(set(artifact_ids)):
            raise ValueError("dataset artifact ids must be unique")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("created_at", None)
        return canonical_sha256(payload)


class DatasetVersionBinding(BaseModel):
    dataset: DatasetIdentity
    dataset_version: DatasetVersion

    @model_validator(mode="after")
    def validate_binding(self):
        if self.dataset.dataset_id != self.dataset_version.dataset_id:
            raise ValueError("DatasetVersion.dataset_id must match DatasetIdentity.dataset_id")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256({
            "dataset_fingerprint_sha256": self.dataset.fingerprint(),
            "dataset_version_fingerprint_sha256": self.dataset_version.fingerprint(),
        })


class FeatureDefinition(BaseModel):
    feature_id: str = Field(min_length=2, max_length=240)
    name: str = Field(min_length=1, max_length=300)
    data_type: str = Field(min_length=1, max_length=120)
    semantic_type: str | None = Field(default=None, max_length=240)
    source_field_refs: list[str] = Field(default_factory=list)
    transformation_ref: str | None = Field(default=None, max_length=300)
    units: str | None = Field(default=None, max_length=120)
    nullable: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class FeatureSet(BaseModel):
    feature_set_id: str = Field(min_length=2, max_length=300)
    dataset_version_ref: str = Field(min_length=2, max_length=300)
    version: str = Field(min_length=1, max_length=240)
    features: list[FeatureDefinition] = Field(default_factory=list)
    target_feature_refs: list[str] = Field(default_factory=list)
    feature_order_significant: bool = False
    created_by_job_ref: str | None = Field(default=None, max_length=300)
    runtime_environment_ref: str | None = Field(default=None, max_length=300)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_features(self):
        ids = [item.feature_id for item in self.features]
        if len(ids) != len(set(ids)):
            raise ValueError("feature ids must be unique")
        known = set(ids)
        missing_targets = [item for item in self.target_feature_refs if item not in known]
        if missing_targets:
            raise ValueError(
                "target_feature_refs must identify features in this feature set: "
                + ", ".join(missing_targets)
            )
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("created_at", None)
        if not self.feature_order_significant:
            payload["features"] = sorted(
                payload.get("features", []),
                key=lambda item: item["feature_id"],
            )
        return canonical_sha256(payload)


class TransformationStep(BaseModel):
    transformation_id: str = Field(min_length=2, max_length=300)
    ordinal: int = Field(ge=1)
    operation: str = Field(min_length=1, max_length=300)
    method_ref: str | None = Field(default=None, max_length=300)
    input_refs: list[str] = Field(default_factory=list)
    output_refs: list[str] = Field(default_factory=list)
    parameters: dict[str, Any] = Field(default_factory=dict)
    code_ref: str | None = Field(default=None, max_length=2000)
    code_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    runtime_environment_ref: str | None = Field(default=None, max_length=300)
    computational_job_ref: str | None = Field(default=None, max_length=300)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DatasetSplit(BaseModel):
    split_id: str = Field(min_length=2, max_length=300)
    role: DatasetRole
    dataset_version_ref: str = Field(min_length=2, max_length=300)
    selection_method: Literal[
        "explicit-index",
        "random",
        "stratified",
        "grouped",
        "temporal",
        "spatial",
        "cross-validation",
        "external",
        "other",
    ]
    fraction: float | None = Field(default=None, ge=0.0, le=1.0)
    random_seed: int | None = None
    index_artifact_ref: str | None = Field(default=None, max_length=300)
    criteria: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TrainingLineage(BaseModel):
    training_lineage_id: str = Field(min_length=2, max_length=300)
    ai_model_ref: str = Field(min_length=2, max_length=300)
    ai_model_version_ref: str = Field(min_length=2, max_length=300)
    training_job_ref: str = Field(min_length=2, max_length=300)
    runtime_environment_ref: str | None = Field(default=None, max_length=300)
    source_dataset_version_refs: list[str] = Field(default_factory=list)
    feature_set_ref: str | None = Field(default=None, max_length=300)
    splits: list[DatasetSplit] = Field(default_factory=list)
    transformations: list[TransformationStep] = Field(default_factory=list)
    random_seed: int | None = None
    hyperparameters: dict[str, Any] = Field(default_factory=dict)
    framework: str | None = Field(default=None, max_length=240)
    framework_version: str | None = Field(default=None, max_length=120)
    output_artifact_refs: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_lineage(self):
        split_ids = [item.split_id for item in self.splits]
        if len(split_ids) != len(set(split_ids)):
            raise ValueError("dataset split ids must be unique")
        transformation_ids = [item.transformation_id for item in self.transformations]
        if len(transformation_ids) != len(set(transformation_ids)):
            raise ValueError("transformation ids must be unique")
        ordinals = [item.ordinal for item in self.transformations]
        if ordinals and sorted(ordinals) != list(range(1, len(ordinals) + 1)):
            raise ValueError("transformation ordinals must be contiguous starting at 1")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("created_at", None)
        return canonical_sha256(payload)


class TrainingLineageBundle(BaseModel):
    dataset_bindings: list[DatasetVersionBinding] = Field(default_factory=list)
    feature_sets: list[FeatureSet] = Field(default_factory=list)
    training_lineage: TrainingLineage

    @model_validator(mode="after")
    def validate_bundle(self):
        dataset_refs = {
            item.dataset_version.dataset_version_id
            for item in self.dataset_bindings
        }
        missing = [
            ref for ref in self.training_lineage.source_dataset_version_refs
            if ref not in dataset_refs
        ]
        if missing:
            raise ValueError(
                "training lineage references dataset versions not present in bundle: "
                + ", ".join(missing)
            )

        if self.training_lineage.feature_set_ref:
            feature_set_refs = {item.feature_set_id for item in self.feature_sets}
            if self.training_lineage.feature_set_ref not in feature_set_refs:
                raise ValueError("training lineage feature_set_ref is not present in bundle")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256({
            "datasets": sorted(
                item.fingerprint() for item in self.dataset_bindings
            ),
            "feature_sets": sorted(
                item.fingerprint() for item in self.feature_sets
            ),
            "training_lineage": self.training_lineage.fingerprint(),
        })


def reference_training_lineage() -> TrainingLineageBundle:
    dataset = DatasetIdentity(
        dataset_id="dataset:reference-scientific-regression",
        name="Reference Scientific Regression Dataset",
        modality=DatasetModality.tabular,
        source_refs=["source:reference-observations"],
        provenance={
            "purpose": "Platform Core v3.28.0 training-lineage proof",
            "generic_dataset_registry_duplicated": False,
        },
    )
    dataset_version = DatasetVersion(
        dataset_version_id="dataset-version:reference-scientific-regression:v1",
        dataset_id=dataset.dataset_id,
        version="v1",
        row_count=1000,
        column_count=5,
        content_sha256="a" * 64,
        schema_sha256="b" * 64,
        runtime_environment_ref="environment:reference-python",
        creation_job_ref="job:reference-dataset-preparation",
        artifacts=[
            DatasetArtifact(
                artifact_id="artifact:reference-dataset:data",
                artifact_kind="data",
                content_sha256="a" * 64,
            ),
            DatasetArtifact(
                artifact_id="artifact:reference-dataset:schema",
                artifact_kind="schema",
                content_sha256="b" * 64,
            ),
        ],
    )
    binding = DatasetVersionBinding(
        dataset=dataset,
        dataset_version=dataset_version,
    )

    feature_set = FeatureSet(
        feature_set_id="feature-set:reference-scientific-regression:v1",
        dataset_version_ref=dataset_version.dataset_version_id,
        version="v1",
        features=[
            FeatureDefinition(
                feature_id="feature:x1",
                name="x1",
                data_type="float64",
            ),
            FeatureDefinition(
                feature_id="feature:x2",
                name="x2",
                data_type="float64",
            ),
            FeatureDefinition(
                feature_id="feature:y",
                name="y",
                data_type="float64",
                semantic_type="target",
            ),
        ],
        target_feature_refs=["feature:y"],
        created_by_job_ref="job:reference-feature-engineering",
        runtime_environment_ref="environment:reference-python",
    )

    lineage = TrainingLineage(
        training_lineage_id="training-lineage:reference-scientific-regressor:1.0.0",
        ai_model_ref="ai-model:reference-scientific-regressor",
        ai_model_version_ref="ai-model-version:reference-scientific-regressor:1.0.0",
        training_job_ref="job:reference-model-training",
        runtime_environment_ref="environment:reference-python",
        source_dataset_version_refs=[dataset_version.dataset_version_id],
        feature_set_ref=feature_set.feature_set_id,
        splits=[
            DatasetSplit(
                split_id="split:reference-training",
                role=DatasetRole.training,
                dataset_version_ref=dataset_version.dataset_version_id,
                selection_method="random",
                fraction=0.8,
                random_seed=427,
            ),
            DatasetSplit(
                split_id="split:reference-evaluation",
                role=DatasetRole.evaluation,
                dataset_version_ref=dataset_version.dataset_version_id,
                selection_method="random",
                fraction=0.2,
                random_seed=427,
            ),
        ],
        transformations=[
            TransformationStep(
                transformation_id="transform:standardize-features",
                ordinal=1,
                operation="standardize",
                input_refs=["feature:x1", "feature:x2"],
                output_refs=["feature:x1", "feature:x2"],
                parameters={"with_mean": True, "with_std": True},
                computational_job_ref="job:reference-feature-engineering",
            )
        ],
        random_seed=427,
        hyperparameters={
            "learning_rate": 0.05,
            "max_depth": 4,
            "n_estimators": 200,
        },
        framework="reference",
        framework_version="1.0",
        output_artifact_refs=[
            "artifact:reference-scientific-regressor:weights",
            "artifact:reference-scientific-regressor:config",
        ],
    )

    return TrainingLineageBundle(
        dataset_bindings=[binding],
        feature_sets=[feature_set],
        training_lineage=lineage,
    )


def contract_document() -> dict[str, Any]:
    reference = reference_training_lineage()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "depends_on": [
            AI_MODEL_CONTRACT_VERSION,
            COMPUTATIONAL_JOB_CONTRACT_VERSION,
            ENVIRONMENT_PROVENANCE_CONTRACT_VERSION,
        ],
        "object_types": [
            "DatasetIdentity",
            "DatasetArtifact",
            "DatasetVersion",
            "DatasetVersionBinding",
            "FeatureDefinition",
            "FeatureSet",
            "TransformationStep",
            "DatasetSplit",
            "TrainingLineage",
            "TrainingLineageBundle",
        ],
        "lineage_capabilities": {
            "dataset_identity": True,
            "immutable_dataset_versions": True,
            "content_hashing": True,
            "feature_set_versioning": True,
            "transformation_lineage": True,
            "dataset_split_lineage": True,
            "random_seed_capture": True,
            "hyperparameter_capture": True,
            "training_job_binding": True,
            "runtime_environment_binding": True,
            "ai_model_version_binding": True,
        },
        "integration": {
            "duplicates_generic_dataset_registry": False,
            "ai_model_contract": AI_MODEL_CONTRACT_VERSION,
            "computational_job_contract": COMPUTATIONAL_JOB_CONTRACT_VERSION,
            "environment_contract": ENVIRONMENT_PROVENANCE_CONTRACT_VERSION,
            "knowledge_library_source_refs_supported": True,
        },
        "reference": {
            "training_lineage_id": reference.training_lineage.training_lineage_id,
            "ai_model_version_ref": reference.training_lineage.ai_model_version_ref,
            "bundle_fingerprint_sha256": reference.fingerprint(),
        },
        "boundaries": {
            "core_materializes_datasets": False,
            "core_executes_feature_engineering": False,
            "core_trains_models": False,
            "core_selects_training_data_autonomously": False,
            "workspace_or_runtime_executes_pipeline": True,
            "core_owns_training_lineage_contracts": True,
        },
    }
