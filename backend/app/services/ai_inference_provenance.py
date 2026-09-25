from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256

CORE_RELEASE = "3.29.0"
CONTRACT_VERSION = "sc.core.ai-inference-provenance.v1"
AI_MODEL_CONTRACT_VERSION = "sc.core.ai-model.v1"
AI_TRAINING_LINEAGE_CONTRACT_VERSION = "sc.core.ai-training-lineage.v1"
COMPUTATIONAL_JOB_CONTRACT_VERSION = "sc.core.computational-job.v1"
ENVIRONMENT_PROVENANCE_CONTRACT_VERSION = "sc.core.execution-environment-provenance.v1"


class AIInferenceStatus(str, Enum):
    declared = "declared"
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class AIInputKind(str, Enum):
    text = "text"
    tabular = "tabular"
    image = "image"
    audio = "audio"
    video = "video"
    geospatial = "geospatial"
    time_series = "time-series"
    graph = "graph"
    embedding = "embedding"
    document = "document"
    dataset = "dataset"
    multimodal = "multimodal"
    other = "other"


class AIArtifactKind(str, Enum):
    prediction = "prediction"
    classification = "classification"
    regression = "regression"
    forecast = "forecast"
    embedding = "embedding"
    ranking = "ranking"
    generated_text = "generated-text"
    generated_image = "generated-image"
    generated_audio = "generated-audio"
    generated_video = "generated-video"
    extraction = "extraction"
    summary = "summary"
    table = "table"
    array = "array"
    figure = "figure"
    file = "file"
    report = "report"
    trace = "trace"
    log = "log"
    other = "other"


class AIInferenceInput(BaseModel):
    input_id: str = Field(min_length=2, max_length=300)
    input_kind: AIInputKind
    name: str | None = Field(default=None, max_length=300)
    value: Any = None
    source_ref: str | None = Field(default=None, max_length=1000)
    dataset_version_ref: str | None = Field(default=None, max_length=300)
    artifact_ref: str | None = Field(default=None, max_length=300)
    content_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    media_type: str | None = Field(default=None, max_length=255)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_input_identity(self):
        if (
            self.value is None
            and self.source_ref is None
            and self.dataset_version_ref is None
            and self.artifact_ref is None
        ):
            raise ValueError(
                "inference input requires value, source_ref, dataset_version_ref, or artifact_ref"
            )
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class AIInferenceParameterSet(BaseModel):
    parameter_set_id: str = Field(min_length=2, max_length=300)
    parameters: dict[str, Any] = Field(default_factory=dict)
    random_seed: int | None = None
    deterministic_requested: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class AIArtifactProvenance(BaseModel):
    ai_artifact_id: str = Field(min_length=2, max_length=300)
    artifact_kind: AIArtifactKind
    inference_run_ref: str = Field(min_length=2, max_length=300)
    ai_model_ref: str = Field(min_length=2, max_length=300)
    ai_model_version_ref: str = Field(min_length=2, max_length=300)
    runtime_artifact_ref: str | None = Field(default=None, max_length=300)
    execution_result_ref: str | None = Field(default=None, max_length=300)
    source_input_refs: list[str] = Field(default_factory=list)
    content_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    media_type: str | None = Field(default=None, max_length=255)
    uri: str | None = Field(default=None, max_length=4000)
    scalar_value: Any = None
    structured_value: Any = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_payload(self):
        if (
            self.runtime_artifact_ref is None
            and self.execution_result_ref is None
            and self.content_sha256 is None
            and self.uri is None
            and self.scalar_value is None
            and self.structured_value is None
        ):
            raise ValueError(
                "AI artifact requires a runtime/result reference, content hash, URI, or value"
            )
        if self.ai_model_version_ref.startswith("ai-model-version:") is False:
            raise ValueError("ai_model_version_ref must identify an AI model version")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("created_at", None)
        return canonical_sha256(payload)


class AIInferenceUsage(BaseModel):
    input_units: int | float | None = Field(default=None, ge=0)
    output_units: int | float | None = Field(default=None, ge=0)
    unit_kind: Literal[
        "tokens",
        "rows",
        "samples",
        "images",
        "seconds",
        "bytes",
        "requests",
        "other",
    ] | None = None
    latency_ms: float | None = Field(default=None, ge=0)
    compute_seconds: float | None = Field(default=None, ge=0)
    cost_amount: float | None = Field(default=None, ge=0)
    cost_currency: str | None = Field(default=None, max_length=12)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AIInferenceRun(BaseModel):
    inference_run_id: str = Field(min_length=2, max_length=300)
    status: AIInferenceStatus = AIInferenceStatus.declared
    ai_model_ref: str = Field(min_length=2, max_length=300)
    ai_model_version_ref: str = Field(min_length=2, max_length=300)
    computational_job_ref: str = Field(min_length=2, max_length=300)
    execution_result_ref: str | None = Field(default=None, max_length=300)
    runtime_environment_ref: str | None = Field(default=None, max_length=300)
    provider_ref: str | None = Field(default=None, max_length=300)
    provider_model_identifier: str | None = Field(default=None, max_length=1000)
    operation: str = Field(min_length=1, max_length=300)
    inputs: list[AIInferenceInput] = Field(default_factory=list)
    parameter_set: AIInferenceParameterSet | None = None
    prompt_version_ref: str | None = Field(default=None, max_length=300)
    retrieval_context_ref: str | None = Field(default=None, max_length=300)
    artifacts: list[AIArtifactProvenance] = Field(default_factory=list)
    usage: AIInferenceUsage | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_run(self):
        if self.ai_model_version_ref.startswith("ai-model-version:") is False:
            raise ValueError("ai_model_version_ref must identify an AI model version")

        input_ids = [item.input_id for item in self.inputs]
        if len(input_ids) != len(set(input_ids)):
            raise ValueError("inference input ids must be unique")

        artifact_ids = [item.ai_artifact_id for item in self.artifacts]
        if len(artifact_ids) != len(set(artifact_ids)):
            raise ValueError("AI artifact ids must be unique")

        known_inputs = set(input_ids)
        for artifact in self.artifacts:
            if artifact.inference_run_ref != self.inference_run_id:
                raise ValueError("artifact inference_run_ref must match this run")
            if artifact.ai_model_ref != self.ai_model_ref:
                raise ValueError("artifact ai_model_ref must match this run")
            if artifact.ai_model_version_ref != self.ai_model_version_ref:
                raise ValueError("artifact ai_model_version_ref must match this run")
            unknown_inputs = [
                ref for ref in artifact.source_input_refs if ref not in known_inputs
            ]
            if unknown_inputs:
                raise ValueError(
                    "artifact source_input_refs not present in run inputs: "
                    + ", ".join(unknown_inputs)
                )

        if self.status == AIInferenceStatus.completed and not self.artifacts:
            raise ValueError("completed inference run must contain at least one artifact")

        if (
            self.completed_at is not None
            and self.started_at is not None
            and self.completed_at < self.started_at
        ):
            raise ValueError("completed_at cannot precede started_at")

        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        for key in ("status", "started_at", "completed_at", "created_at", "usage"):
            payload.pop(key, None)
        return canonical_sha256(payload)


class AIInferenceRunBundle(BaseModel):
    inference_run: AIInferenceRun
    training_lineage_ref: str | None = Field(default=None, max_length=300)
    evaluation_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256({
            "inference_run_fingerprint_sha256": self.inference_run.fingerprint(),
            "training_lineage_ref": self.training_lineage_ref,
            "evaluation_refs": sorted(self.evaluation_refs),
            "evidence_refs": sorted(self.evidence_refs),
            "metadata": self.metadata,
        })


class AIInferenceComparisonDifference(BaseModel):
    field: str
    left: Any = None
    right: Any = None


class AIInferenceComparison(BaseModel):
    exact_match: bool
    left_fingerprint_sha256: str
    right_fingerprint_sha256: str
    differences: list[AIInferenceComparisonDifference] = Field(default_factory=list)


def compare_inference_runs(
    left: AIInferenceRun,
    right: AIInferenceRun,
) -> AIInferenceComparison:
    fields = (
        "ai_model_ref",
        "ai_model_version_ref",
        "computational_job_ref",
        "execution_result_ref",
        "runtime_environment_ref",
        "provider_ref",
        "provider_model_identifier",
        "operation",
        "inputs",
        "parameter_set",
        "prompt_version_ref",
        "retrieval_context_ref",
        "artifacts",
    )
    differences: list[AIInferenceComparisonDifference] = []
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
                AIInferenceComparisonDifference(
                    field=field_name,
                    left=a,
                    right=b,
                )
            )

    return AIInferenceComparison(
        exact_match=not differences,
        left_fingerprint_sha256=left.fingerprint(),
        right_fingerprint_sha256=right.fingerprint(),
        differences=differences,
    )


def reference_inference_run() -> AIInferenceRunBundle:
    run_id = "inference-run:reference-scientific-regressor:001"
    model_ref = "ai-model:reference-scientific-regressor"
    model_version_ref = "ai-model-version:reference-scientific-regressor:1.0.0"

    inputs = [
        AIInferenceInput(
            input_id="inference-input:reference-row-001",
            input_kind=AIInputKind.tabular,
            name="reference-row",
            value={"x1": 1.5, "x2": 3.25},
            content_sha256="a" * 64,
        )
    ]

    artifact = AIArtifactProvenance(
        ai_artifact_id="ai-artifact:reference-prediction-001",
        artifact_kind=AIArtifactKind.prediction,
        inference_run_ref=run_id,
        ai_model_ref=model_ref,
        ai_model_version_ref=model_version_ref,
        execution_result_ref="result:reference-inference-001",
        source_input_refs=[inputs[0].input_id],
        content_sha256="b" * 64,
        scalar_value=7.8125,
        provenance={
            "purpose": "Platform Core v3.29.0 inference provenance proof",
        },
    )

    run = AIInferenceRun(
        inference_run_id=run_id,
        status=AIInferenceStatus.completed,
        ai_model_ref=model_ref,
        ai_model_version_ref=model_version_ref,
        computational_job_ref="job:reference-inference-001",
        execution_result_ref="result:reference-inference-001",
        runtime_environment_ref="environment:reference-python",
        provider_ref="provider:sustainable-catalyst-local",
        provider_model_identifier="reference-scientific-regressor@1.0.0",
        operation="predict",
        inputs=inputs,
        parameter_set=AIInferenceParameterSet(
            parameter_set_id="inference-parameters:reference-001",
            parameters={"output": "scalar"},
            random_seed=429,
            deterministic_requested=True,
        ),
        artifacts=[artifact],
        usage=AIInferenceUsage(
            input_units=1,
            output_units=1,
            unit_kind="rows",
            latency_ms=12.5,
        ),
        started_at=datetime(2026, 9, 25, 12, 0, tzinfo=timezone.utc),
        completed_at=datetime(2026, 9, 25, 12, 0, 1, tzinfo=timezone.utc),
        provenance={
            "ai_model_contract": AI_MODEL_CONTRACT_VERSION,
            "training_lineage_contract": AI_TRAINING_LINEAGE_CONTRACT_VERSION,
            "computational_job_contract": COMPUTATIONAL_JOB_CONTRACT_VERSION,
        },
    )

    return AIInferenceRunBundle(
        inference_run=run,
        training_lineage_ref=(
            "training-lineage:reference-scientific-regressor:1.0.0"
        ),
        evidence_refs=["evidence:reference-inference-proof"],
    )


def contract_document() -> dict[str, Any]:
    reference = reference_inference_run()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "depends_on": [
            AI_MODEL_CONTRACT_VERSION,
            AI_TRAINING_LINEAGE_CONTRACT_VERSION,
            COMPUTATIONAL_JOB_CONTRACT_VERSION,
            ENVIRONMENT_PROVENANCE_CONTRACT_VERSION,
        ],
        "object_types": [
            "AIInferenceInput",
            "AIInferenceParameterSet",
            "AIArtifactProvenance",
            "AIInferenceUsage",
            "AIInferenceRun",
            "AIInferenceRunBundle",
            "AIInferenceComparison",
        ],
        "provenance_capabilities": {
            "exact_model_version_binding": True,
            "computational_job_binding": True,
            "execution_result_binding": True,
            "runtime_environment_binding": True,
            "provider_binding": True,
            "input_fingerprinting": True,
            "parameter_set_fingerprinting": True,
            "artifact_content_hashing": True,
            "source_input_to_artifact_lineage": True,
            "usage_and_latency_capture": True,
            "prompt_version_ref_reserved_for_v3_30": True,
            "retrieval_context_ref_reserved_for_v3_30": True,
        },
        "integration": {
            "duplicates_runtime_artifact_model": False,
            "runtime_artifact_refs_supported": True,
            "training_lineage_refs_supported": True,
            "evaluation_refs_supported": True,
            "evidence_refs_supported": True,
        },
        "reference": {
            "inference_run_id": reference.inference_run.inference_run_id,
            "ai_model_version_ref": reference.inference_run.ai_model_version_ref,
            "bundle_fingerprint_sha256": reference.fingerprint(),
        },
        "boundaries": {
            "core_executes_inference": False,
            "core_selects_model_autonomously": False,
            "core_generates_artifacts": False,
            "core_prices_provider_usage": False,
            "workspace_or_runtime_executes_inference": True,
            "core_owns_inference_identity_lineage_and_contracts": True,
        },
    }
