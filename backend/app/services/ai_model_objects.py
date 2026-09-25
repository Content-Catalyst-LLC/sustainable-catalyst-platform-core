from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256

CORE_RELEASE = "3.27.0"
CONTRACT_VERSION = "sc.core.ai-model.v1"


class AIModelKind(str, Enum):
    classical_ml = "classical-ml"
    neural_network = "neural-network"
    foundation_model = "foundation-model"
    embedding_model = "embedding-model"
    reranker = "reranker"
    generative_model = "generative-model"
    multimodal_model = "multimodal-model"
    scientific_ml = "scientific-ml"
    hybrid = "hybrid"


class AIModelStatus(str, Enum):
    draft = "draft"
    registered = "registered"
    active = "active"
    deprecated = "deprecated"
    retired = "retired"


class AIProviderKind(str, Enum):
    open_source = "open-source"
    local = "local"
    self_hosted = "self-hosted"
    managed_api = "managed-api"
    remote_compute = "remote-compute"


class AIModelProvider(BaseModel):
    provider_id: str = Field(min_length=2, max_length=240)
    name: str = Field(min_length=1, max_length=240)
    provider_kind: AIProviderKind
    organization: str | None = Field(default=None, max_length=240)
    endpoint_ref: str | None = Field(default=None, max_length=2000)
    license_ref: str | None = Field(default=None, max_length=1000)
    terms_ref: str | None = Field(default=None, max_length=1000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AIModelCapability(BaseModel):
    capability_key: str = Field(min_length=2, max_length=180)
    task: Literal[
        "classification",
        "regression",
        "forecasting",
        "clustering",
        "anomaly-detection",
        "embedding",
        "ranking",
        "generation",
        "summarization",
        "extraction",
        "question-answering",
        "vision",
        "audio",
        "multimodal",
        "scientific-ml",
        "other",
    ]
    input_modalities: list[str] = Field(default_factory=list)
    output_modalities: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AIModel(BaseModel):
    model_id: str = Field(min_length=2, max_length=240)
    name: str = Field(min_length=1, max_length=300)
    family: str | None = Field(default=None, max_length=300)
    model_kind: AIModelKind
    provider: AIModelProvider
    status: AIModelStatus = AIModelStatus.registered
    capabilities: list[AIModelCapability] = Field(default_factory=list)
    research_model_ref: str | None = Field(default=None, max_length=240)
    predictive_model_ref: str | None = Field(default=None, max_length=240)
    parent_model_ref: str | None = Field(default=None, max_length=240)
    description: str | None = Field(default=None, max_length=10000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_capabilities(self):
        keys = [item.capability_key for item in self.capabilities]
        if len(keys) != len(set(keys)):
            raise ValueError("AI model capability keys must be unique")
        if self.parent_model_ref == self.model_id:
            raise ValueError("parent_model_ref cannot reference the model itself")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("created_at", None)
        return canonical_sha256(payload)


class AIModelArtifact(BaseModel):
    artifact_id: str = Field(min_length=2, max_length=240)
    artifact_kind: Literal[
        "weights",
        "checkpoint",
        "config",
        "tokenizer",
        "vocabulary",
        "preprocessor",
        "feature-pipeline",
        "adapter",
        "quantization",
        "architecture",
        "model-card",
        "license",
        "other",
    ]
    uri: str | None = Field(default=None, max_length=4000)
    content_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    size_bytes: int | None = Field(default=None, ge=0)
    media_type: str | None = Field(default=None, max_length=255)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AIModelVersion(BaseModel):
    model_version_id: str = Field(min_length=2, max_length=300)
    model_id: str = Field(min_length=2, max_length=240)
    version: str = Field(min_length=1, max_length=240)
    status: AIModelStatus = AIModelStatus.registered
    architecture: str | None = Field(default=None, max_length=500)
    framework: str | None = Field(default=None, max_length=240)
    framework_version: str | None = Field(default=None, max_length=120)
    parameter_count: int | None = Field(default=None, ge=0)
    precision: str | None = Field(default=None, max_length=100)
    context_window: int | None = Field(default=None, ge=1)
    weights_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    config_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    tokenizer_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    training_dataset_refs: list[str] = Field(default_factory=list)
    evaluation_dataset_refs: list[str] = Field(default_factory=list)
    source_commit: str | None = Field(default=None, max_length=240)
    runtime_environment_ref: str | None = Field(default=None, max_length=240)
    training_job_ref: str | None = Field(default=None, max_length=240)
    artifacts: list[AIModelArtifact] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_version(self):
        ids = [item.artifact_id for item in self.artifacts]
        if len(ids) != len(set(ids)):
            raise ValueError("AI model artifact ids must be unique")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("created_at", None)
        return canonical_sha256(payload)


class AIModelVersionBinding(BaseModel):
    model: AIModel
    model_version: AIModelVersion

    @model_validator(mode="after")
    def validate_binding(self):
        if self.model.model_id != self.model_version.model_id:
            raise ValueError("AIModelVersion.model_id must match AIModel.model_id")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256({
            "model_fingerprint_sha256": self.model.fingerprint(),
            "model_version_fingerprint_sha256": self.model_version.fingerprint(),
        })


class AIModelVersionDifference(BaseModel):
    field: str
    left: Any = None
    right: Any = None


class AIModelVersionComparison(BaseModel):
    exact_match: bool
    left_fingerprint_sha256: str
    right_fingerprint_sha256: str
    differences: list[AIModelVersionDifference] = Field(default_factory=list)


def compare_model_versions(
    left: AIModelVersion,
    right: AIModelVersion,
) -> AIModelVersionComparison:
    fields = (
        "model_id",
        "version",
        "architecture",
        "framework",
        "framework_version",
        "parameter_count",
        "precision",
        "context_window",
        "weights_sha256",
        "config_sha256",
        "tokenizer_sha256",
        "training_dataset_refs",
        "evaluation_dataset_refs",
        "source_commit",
        "runtime_environment_ref",
        "training_job_ref",
        "artifacts",
    )
    differences: list[AIModelVersionDifference] = []
    for field_name in fields:
        a = getattr(left, field_name)
        b = getattr(right, field_name)
        if a != b:
            if hasattr(a, "model_dump"):
                a = a.model_dump(mode="json", exclude_none=True)
            if hasattr(b, "model_dump"):
                b = b.model_dump(mode="json", exclude_none=True)
            if isinstance(a, list):
                a = [
                    item.model_dump(mode="json", exclude_none=True)
                    if hasattr(item, "model_dump") else item
                    for item in a
                ]
            if isinstance(b, list):
                b = [
                    item.model_dump(mode="json", exclude_none=True)
                    if hasattr(item, "model_dump") else item
                    for item in b
                ]
            differences.append(
                AIModelVersionDifference(
                    field=field_name,
                    left=a,
                    right=b,
                )
            )
    return AIModelVersionComparison(
        exact_match=not differences,
        left_fingerprint_sha256=left.fingerprint(),
        right_fingerprint_sha256=right.fingerprint(),
        differences=differences,
    )


def reference_ai_model() -> AIModelVersionBinding:
    model = AIModel(
        model_id="ai-model:reference-scientific-regressor",
        name="Reference Scientific Regressor",
        family="Sustainable Catalyst Reference Models",
        model_kind=AIModelKind.classical_ml,
        provider=AIModelProvider(
            provider_id="provider:sustainable-catalyst-local",
            name="Sustainable Catalyst Local Runtime",
            provider_kind=AIProviderKind.local,
            organization="Content Catalyst LLC",
        ),
        status=AIModelStatus.registered,
        capabilities=[
            AIModelCapability(
                capability_key="supervised-regression",
                task="regression",
                input_modalities=["tabular"],
                output_modalities=["scalar"],
            )
        ],
        research_model_ref="research-model:reference-scientific-regressor",
        predictive_model_ref="predictive-model:reference-scientific-regressor",
        provenance={
            "purpose": "Platform Core v3.27.0 AI model contract proof",
            "generic_model_registry_duplicated": False,
        },
    )
    version = AIModelVersion(
        model_version_id="ai-model-version:reference-scientific-regressor:1.0.0",
        model_id=model.model_id,
        version="1.0.0",
        architecture="gradient-boosted-regression",
        framework="reference",
        framework_version="1.0",
        parameter_count=1000,
        precision="float64",
        weights_sha256="a" * 64,
        config_sha256="b" * 64,
        training_dataset_refs=["dataset-version:reference-training:v1"],
        evaluation_dataset_refs=["dataset-version:reference-evaluation:v1"],
        source_commit="reference-commit",
        runtime_environment_ref="environment:reference-python",
        artifacts=[
            AIModelArtifact(
                artifact_id="artifact:reference-scientific-regressor:weights",
                artifact_kind="weights",
                content_sha256="a" * 64,
            ),
            AIModelArtifact(
                artifact_id="artifact:reference-scientific-regressor:config",
                artifact_kind="config",
                content_sha256="b" * 64,
            ),
        ],
        provenance={
            "model_id": model.model_id,
            "version_semantics": "immutable-content-addressed",
        },
    )
    return AIModelVersionBinding(model=model, model_version=version)


def contract_document() -> dict[str, Any]:
    reference = reference_ai_model()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "object_types": [
            "AIModelProvider",
            "AIModelCapability",
            "AIModel",
            "AIModelArtifact",
            "AIModelVersion",
            "AIModelVersionBinding",
            "AIModelVersionComparison",
        ],
        "identity_rules": {
            "model_identity_stable_across_versions": True,
            "model_version_identity_immutable": True,
            "content_hashes_sha256": True,
            "provider_identity_explicit": True,
            "training_dataset_refs_supported": True,
            "evaluation_dataset_refs_supported": True,
            "runtime_environment_ref_supported": True,
            "training_job_ref_supported": True,
        },
        "integration": {
            "specializes_existing_research_model": True,
            "specializes_existing_predictive_model": True,
            "duplicates_generic_model_registry": False,
            "future_training_jobs_use_computational_job_contract": True,
            "future_inference_runs_bind_model_version": True,
        },
        "reference": {
            "model_id": reference.model.model_id,
            "model_version_id": reference.model_version.model_version_id,
            "binding_fingerprint_sha256": reference.fingerprint(),
        },
        "boundaries": {
            "core_trains_models": False,
            "core_runs_inference": False,
            "core_downloads_weights": False,
            "core_selects_model_autonomously": False,
            "core_certifies_model_quality": False,
            "core_owns_model_identity_lineage_and_contracts": True,
        },
    }
