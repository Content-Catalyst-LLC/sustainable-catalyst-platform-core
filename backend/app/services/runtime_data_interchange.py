from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256

CORE_RELEASE = "3.39.0"
CONTRACT_VERSION = "sc.core.runtime-data-interchange.v1"

R_RUNTIME_CONTRACT = "sc.core.r-runtime-migration.v1"
RUNTIME_OBJECT_CONTRACT = "sc.core.computational-runtime-object.v1"
RUNTIME_ADAPTER_CONTRACT = "sc.core.runtime-adapter.v1"
COMPUTATIONAL_JOB_CONTRACT = "sc.core.computational-job.v1"
ENVIRONMENT_PROVENANCE_CONTRACT = "sc.core.execution-environment-provenance.v1"
SCIENTIFIC_REGISTRY_CONTRACT = "sc.core.scientific-result-artifact-registry.v1"

REFERENCE_R_RUNTIME = "sc-runtime-r"
REFERENCE_R_VERSION = "1.0.0"
REFERENCE_JULIA_RUNTIME = "catalyst-julia-runtime"
REFERENCE_JULIA_VERSION = "0.3.0"


class InterchangeFormat(str, Enum):
    json = "json"
    csv = "csv"
    arrow_ipc_file = "arrow-ipc-file"
    arrow_ipc_stream = "arrow-ipc-stream"
    parquet = "parquet"
    npy = "npy"
    npz = "npz"
    feather = "feather"
    text = "text"
    binary = "binary"
    other = "other"


class DataShapeKind(str, Enum):
    scalar = "scalar"
    vector = "vector"
    matrix = "matrix"
    table = "table"
    tensor = "tensor"
    record = "record"
    collection = "collection"
    opaque = "opaque"


class CanonicalScalarType(str, Enum):
    boolean = "boolean"
    int8 = "int8"
    int16 = "int16"
    int32 = "int32"
    int64 = "int64"
    uint8 = "uint8"
    uint16 = "uint16"
    uint32 = "uint32"
    uint64 = "uint64"
    float32 = "float32"
    float64 = "float64"
    decimal = "decimal"
    string = "string"
    binary = "binary"
    date = "date"
    time = "time"
    timestamp = "timestamp"
    duration = "duration"
    categorical = "categorical"
    unknown = "unknown"


class NullRepresentation(str, Enum):
    native = "native"
    null = "null"
    na = "na"
    nan = "nan"
    empty = "empty"
    sentinel = "sentinel"


class Endianness(str, Enum):
    little = "little"
    big = "big"
    native = "native"
    not_applicable = "not-applicable"


class InterchangeStatus(str, Enum):
    declared = "declared"
    prepared = "prepared"
    transferring = "transferring"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class VerificationStatus(str, Enum):
    not_run = "not-run"
    passed = "passed"
    warning = "warning"
    failed = "failed"


class LossPolicy(str, Enum):
    forbid = "forbid"
    warn = "warn"
    allow = "allow"


class DataFieldSchema(BaseModel):
    field_id: str = Field(min_length=1, max_length=300)
    name: str = Field(min_length=1, max_length=300)
    canonical_type: CanonicalScalarType
    nullable: bool = True
    unit: str | None = Field(default=None, max_length=200)
    logical_type: str | None = Field(default=None, max_length=300)
    categories: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class DataInterchangeSchema(BaseModel):
    schema_id: str = Field(min_length=2, max_length=500)
    shape_kind: DataShapeKind
    fields: list[DataFieldSchema] = Field(default_factory=list)
    dimensions: list[int] = Field(default_factory=list)
    row_count: int | None = Field(default=None, ge=0)
    column_count: int | None = Field(default=None, ge=0)
    endianness: Endianness = Endianness.not_applicable
    null_representation: NullRepresentation = NullRepresentation.native
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_schema(self):
        field_ids = [item.field_id for item in self.fields]
        names = [item.name for item in self.fields]
        if len(field_ids) != len(set(field_ids)):
            raise ValueError("interchange schema field ids must be unique")
        if len(names) != len(set(names)):
            raise ValueError("interchange schema field names must be unique")

        if self.shape_kind == DataShapeKind.table:
            if not self.fields:
                raise ValueError("table interchange schema requires fields")
            if self.column_count is not None and self.column_count != len(self.fields):
                raise ValueError("table column_count must match field count")

        if self.shape_kind in {DataShapeKind.vector, DataShapeKind.matrix, DataShapeKind.tensor}:
            if not self.dimensions:
                raise ValueError("array-like interchange schema requires dimensions")
            if any(value < 0 for value in self.dimensions):
                raise ValueError("interchange dimensions cannot be negative")

        if self.shape_kind == DataShapeKind.matrix and len(self.dimensions) != 2:
            raise ValueError("matrix interchange schema requires exactly two dimensions")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RuntimeTypeMapping(BaseModel):
    mapping_id: str = Field(min_length=2, max_length=500)
    runtime_ref: str = Field(min_length=2, max_length=500)
    runtime_type: str = Field(min_length=1, max_length=300)
    canonical_type: CanonicalScalarType
    lossless: bool = True
    notes: str | None = Field(default=None, max_length=5000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RuntimeInterchangeProfile(BaseModel):
    profile_id: str = Field(min_length=2, max_length=500)
    runtime_ref: str = Field(min_length=2, max_length=500)
    runtime_version: str = Field(min_length=1, max_length=200)
    readable_formats: list[InterchangeFormat] = Field(default_factory=list)
    writable_formats: list[InterchangeFormat] = Field(default_factory=list)
    supported_shapes: list[DataShapeKind] = Field(default_factory=list)
    type_mappings: list[RuntimeTypeMapping] = Field(default_factory=list)
    max_rank: int | None = Field(default=None, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_profile(self):
        if not self.readable_formats:
            raise ValueError("runtime interchange profile requires readable formats")
        if not self.writable_formats:
            raise ValueError("runtime interchange profile requires writable formats")
        if not self.supported_shapes:
            raise ValueError("runtime interchange profile requires supported shapes")

        mapping_ids = [item.mapping_id for item in self.type_mappings]
        if len(mapping_ids) != len(set(mapping_ids)):
            raise ValueError("runtime type mapping ids must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class DataInterchangeArtifact(BaseModel):
    interchange_artifact_id: str = Field(min_length=2, max_length=500)
    logical_data_ref: str = Field(min_length=2, max_length=1000)
    format: InterchangeFormat
    uri: str = Field(min_length=2, max_length=4000)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    data_schema: DataInterchangeSchema
    media_type: str | None = Field(default=None, max_length=300)
    compression: str | None = Field(default=None, max_length=200)
    size_bytes: int | None = Field(default=None, ge=0)
    producer_runtime_ref: str | None = Field(default=None, max_length=500)
    producer_runtime_version: str | None = Field(default=None, max_length=200)
    producer_job_ref: str | None = Field(default=None, max_length=500)
    producer_environment_ref: str | None = Field(default=None, max_length=500)
    source_artifact_refs: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("created_at", None)
        return canonical_sha256(payload)


class DataInterchangeNegotiationRequest(BaseModel):
    source_profile: RuntimeInterchangeProfile
    target_profile: RuntimeInterchangeProfile
    required_shape: DataShapeKind
    required_types: list[CanonicalScalarType] = Field(default_factory=list)
    preferred_formats: list[InterchangeFormat] = Field(default_factory=list)
    require_lossless: bool = True


class DataInterchangeNegotiationResult(BaseModel):
    source_runtime_ref: str
    target_runtime_ref: str
    candidate_formats: list[InterchangeFormat] = Field(default_factory=list)
    rejected_formats: dict[str, list[str]] = Field(default_factory=dict)
    compatible: bool
    selection_mode: str = "candidate-discovery-only"
    selected_format: InterchangeFormat | None = None

    @model_validator(mode="after")
    def validate_selection_mode(self):
        if self.selection_mode != "candidate-discovery-only":
            raise ValueError("Core interchange negotiation is candidate-discovery-only")
        if self.selected_format is not None:
            raise ValueError("Core must not autonomously select an interchange format")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class DataInterchangeConversionSpec(BaseModel):
    conversion_spec_id: str = Field(min_length=2, max_length=500)
    source_artifact_ref: str = Field(min_length=2, max_length=1000)
    source_format: InterchangeFormat
    target_format: InterchangeFormat
    target_schema_ref: str = Field(min_length=2, max_length=1000)
    source_runtime_ref: str | None = Field(default=None, max_length=500)
    target_runtime_ref: str | None = Field(default=None, max_length=500)
    converter_ref: str | None = Field(default=None, max_length=500)
    computational_job_ref: str | None = Field(default=None, max_length=500)
    environment_ref: str | None = Field(default=None, max_length=500)
    loss_policy: LossPolicy = LossPolicy.forbid
    null_policy: str = Field(default="preserve", min_length=1, max_length=200)
    categorical_policy: str = Field(default="preserve", min_length=1, max_length=200)
    timestamp_policy: str = Field(default="preserve-timezone", min_length=1, max_length=200)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class DataInterchangeVerification(BaseModel):
    verification_id: str = Field(min_length=2, max_length=500)
    source_artifact_ref: str = Field(min_length=2, max_length=1000)
    target_artifact_ref: str = Field(min_length=2, max_length=1000)
    status: VerificationStatus = VerificationStatus.not_run
    source_schema_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    target_schema_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    row_count_match: bool | None = None
    column_count_match: bool | None = None
    type_compatibility_passed: bool | None = None
    null_semantics_preserved: bool | None = None
    categorical_semantics_preserved: bool | None = None
    numerical_tolerance: float | None = Field(default=None, ge=0.0)
    verification_job_ref: str | None = Field(default=None, max_length=500)
    notes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class DataInterchangeTransfer(BaseModel):
    transfer_id: str = Field(min_length=2, max_length=500)
    source_artifact: DataInterchangeArtifact
    target_artifact: DataInterchangeArtifact
    source_runtime_ref: str = Field(min_length=2, max_length=500)
    target_runtime_ref: str = Field(min_length=2, max_length=500)
    conversion_spec: DataInterchangeConversionSpec | None = None
    verification: DataInterchangeVerification
    status: InterchangeStatus = InterchangeStatus.declared
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_transfer(self):
        if self.source_artifact.logical_data_ref != self.target_artifact.logical_data_ref:
            raise ValueError("interchange transfer must preserve logical_data_ref")
        if self.verification.source_artifact_ref != self.source_artifact.interchange_artifact_id:
            raise ValueError("verification source artifact mismatch")
        if self.verification.target_artifact_ref != self.target_artifact.interchange_artifact_id:
            raise ValueError("verification target artifact mismatch")
        if (
            self.status == InterchangeStatus.completed
            and self.verification.status not in {VerificationStatus.passed, VerificationStatus.warning}
        ):
            raise ValueError("completed interchange transfer requires verification")
        if self.completed_at is not None and self.status != InterchangeStatus.completed:
            raise ValueError("completed_at requires completed transfer status")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("status", None)
        payload.pop("created_at", None)
        payload.pop("completed_at", None)
        return canonical_sha256(payload)


class RuntimeDataInterchangeBundle(BaseModel):
    bundle_id: str = Field(min_length=2, max_length=500)
    profiles: list[RuntimeInterchangeProfile] = Field(default_factory=list)
    transfers: list[DataInterchangeTransfer] = Field(default_factory=list)
    source_object_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_bundle(self):
        profile_ids = [item.profile_id for item in self.profiles]
        if len(profile_ids) != len(set(profile_ids)):
            raise ValueError("runtime interchange profile ids must be unique")

        transfer_ids = [item.transfer_id for item in self.transfers]
        if len(transfer_ids) != len(set(transfer_ids)):
            raise ValueError("runtime interchange transfer ids must be unique")

        runtime_refs = {item.runtime_ref for item in self.profiles}
        for transfer in self.transfers:
            if transfer.source_runtime_ref not in runtime_refs:
                raise ValueError("transfer source runtime missing from bundle profiles")
            if transfer.target_runtime_ref not in runtime_refs:
                raise ValueError("transfer target runtime missing from bundle profiles")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256({
            "bundle_id": self.bundle_id,
            "profile_fingerprints": sorted(item.fingerprint() for item in self.profiles),
            "transfer_fingerprints": sorted(item.fingerprint() for item in self.transfers),
            "source_object_refs": sorted(self.source_object_refs),
            "metadata": self.metadata,
        })


def negotiate_interchange(
    request: DataInterchangeNegotiationRequest,
) -> DataInterchangeNegotiationResult:
    source_writable = set(request.source_profile.writable_formats)
    target_readable = set(request.target_profile.readable_formats)
    common = source_writable & target_readable

    rejected: dict[str, list[str]] = {}

    if request.required_shape not in request.source_profile.supported_shapes:
        rejected["source-shape"] = [
            f"{request.source_profile.runtime_ref} does not declare {request.required_shape.value}"
        ]
    if request.required_shape not in request.target_profile.supported_shapes:
        rejected["target-shape"] = [
            f"{request.target_profile.runtime_ref} does not declare {request.required_shape.value}"
        ]

    required_types = set(request.required_types)
    for profile, label in [
        (request.source_profile, "source-types"),
        (request.target_profile, "target-types"),
    ]:
        supported = {mapping.canonical_type for mapping in profile.type_mappings}
        missing = sorted(item.value for item in required_types - supported)
        if missing:
            rejected[label] = missing

    preferred = [fmt for fmt in request.preferred_formats if fmt in common]
    remaining = sorted((common - set(preferred)), key=lambda item: item.value)
    candidates = preferred + remaining

    compatible = bool(candidates) and not any(
        key in rejected for key in ("source-shape", "target-shape", "source-types", "target-types")
    )

    return DataInterchangeNegotiationResult(
        source_runtime_ref=request.source_profile.runtime_ref,
        target_runtime_ref=request.target_profile.runtime_ref,
        candidate_formats=candidates if compatible else [],
        rejected_formats=rejected,
        compatible=compatible,
    )


def to_scientific_artifact_payload(
    artifact: DataInterchangeArtifact,
) -> dict[str, Any]:
    kind_map = {
        InterchangeFormat.json: "json",
        InterchangeFormat.csv: "csv",
        InterchangeFormat.parquet: "parquet",
        InterchangeFormat.arrow_ipc_file: "binary",
        InterchangeFormat.arrow_ipc_stream: "binary",
        InterchangeFormat.feather: "binary",
        InterchangeFormat.npy: "binary",
        InterchangeFormat.npz: "binary",
        InterchangeFormat.text: "other",
        InterchangeFormat.binary: "binary",
        InterchangeFormat.other: "other",
    }
    return {
        "artifact_id": f"scientific-artifact:{artifact.interchange_artifact_id}",
        "artifact_kind": kind_map[artifact.format],
        "uri": artifact.uri,
        "content_sha256": artifact.content_sha256,
        "media_type": artifact.media_type,
        "size_bytes": artifact.size_bytes,
        "source_contract": CONTRACT_VERSION,
        "source_object_ref": artifact.interchange_artifact_id,
        "metadata": {
            "logical_data_ref": artifact.logical_data_ref,
            "schema_fingerprint_sha256": artifact.data_schema.fingerprint(),
            "producer_runtime_ref": artifact.producer_runtime_ref,
            "interchange_format": artifact.format.value,
        },
    }


def _type_mappings(runtime_ref: str) -> list[RuntimeTypeMapping]:
    if runtime_ref == REFERENCE_R_RUNTIME:
        return [
            RuntimeTypeMapping(
                mapping_id="type-map:r:logical",
                runtime_ref=runtime_ref,
                runtime_type="logical",
                canonical_type=CanonicalScalarType.boolean,
            ),
            RuntimeTypeMapping(
                mapping_id="type-map:r:integer",
                runtime_ref=runtime_ref,
                runtime_type="integer",
                canonical_type=CanonicalScalarType.int32,
            ),
            RuntimeTypeMapping(
                mapping_id="type-map:r:double",
                runtime_ref=runtime_ref,
                runtime_type="double",
                canonical_type=CanonicalScalarType.float64,
            ),
            RuntimeTypeMapping(
                mapping_id="type-map:r:character",
                runtime_ref=runtime_ref,
                runtime_type="character",
                canonical_type=CanonicalScalarType.string,
            ),
        ]

    if runtime_ref == REFERENCE_JULIA_RUNTIME:
        return [
            RuntimeTypeMapping(
                mapping_id="type-map:julia:Bool",
                runtime_ref=runtime_ref,
                runtime_type="Bool",
                canonical_type=CanonicalScalarType.boolean,
            ),
            RuntimeTypeMapping(
                mapping_id="type-map:julia:Int64",
                runtime_ref=runtime_ref,
                runtime_type="Int64",
                canonical_type=CanonicalScalarType.int64,
            ),
            RuntimeTypeMapping(
                mapping_id="type-map:julia:Float64",
                runtime_ref=runtime_ref,
                runtime_type="Float64",
                canonical_type=CanonicalScalarType.float64,
            ),
            RuntimeTypeMapping(
                mapping_id="type-map:julia:String",
                runtime_ref=runtime_ref,
                runtime_type="String",
                canonical_type=CanonicalScalarType.string,
            ),
        ]

    raise ValueError(f"unknown reference runtime: {runtime_ref}")


def reference_runtime_profiles() -> list[RuntimeInterchangeProfile]:
    return [
        RuntimeInterchangeProfile(
            profile_id="interchange-profile:sc-runtime-r:1.0.0",
            runtime_ref=REFERENCE_R_RUNTIME,
            runtime_version=REFERENCE_R_VERSION,
            readable_formats=[InterchangeFormat.json, InterchangeFormat.csv],
            writable_formats=[InterchangeFormat.json, InterchangeFormat.csv],
            supported_shapes=[
                DataShapeKind.scalar,
                DataShapeKind.vector,
                DataShapeKind.matrix,
                DataShapeKind.table,
            ],
            type_mappings=_type_mappings(REFERENCE_R_RUNTIME),
            max_rank=2,
            metadata={
                "declared_from_provider": "sc-runtime-r@1.0.0",
                "arrow_parquet_direct_support": False,
            },
        ),
        RuntimeInterchangeProfile(
            profile_id="interchange-profile:catalyst-julia-runtime:0.3.0",
            runtime_ref=REFERENCE_JULIA_RUNTIME,
            runtime_version=REFERENCE_JULIA_VERSION,
            readable_formats=[InterchangeFormat.json],
            writable_formats=[InterchangeFormat.json],
            supported_shapes=[
                DataShapeKind.scalar,
                DataShapeKind.vector,
                DataShapeKind.matrix,
                DataShapeKind.table,
            ],
            type_mappings=_type_mappings(REFERENCE_JULIA_RUNTIME),
            max_rank=2,
            metadata={
                "declared_from_provider": "catalyst-julia-runtime@0.3.0",
                "arrow_parquet_direct_support": False,
            },
        ),
    ]


def reference_runtime_data_interchange_bundle() -> RuntimeDataInterchangeBundle:
    profiles = reference_runtime_profiles()

    schema = DataInterchangeSchema(
        schema_id="interchange-schema:reference-two-column-table:v1",
        shape_kind=DataShapeKind.table,
        fields=[
            DataFieldSchema(
                field_id="field:x",
                name="x",
                canonical_type=CanonicalScalarType.float64,
                nullable=False,
            ),
            DataFieldSchema(
                field_id="field:y",
                name="y",
                canonical_type=CanonicalScalarType.float64,
                nullable=False,
            ),
        ],
        row_count=5,
        column_count=2,
        null_representation=NullRepresentation.null,
    )

    logical_ref = "logical-data:reference-regression-table:v1"
    source = DataInterchangeArtifact(
        interchange_artifact_id="interchange-artifact:r-json:reference-regression:v1",
        logical_data_ref=logical_ref,
        format=InterchangeFormat.json,
        uri="core-ref://interchange/r/reference-regression.json",
        content_sha256="a" * 64,
        data_schema=schema,
        media_type="application/json",
        size_bytes=128,
        producer_runtime_ref=REFERENCE_R_RUNTIME,
        producer_runtime_version=REFERENCE_R_VERSION,
        producer_job_ref="job:reference-r-data-export",
        producer_environment_ref="environment:reference-r-runtime-1.0",
        provenance={"source_runtime": "R"},
    )

    target = DataInterchangeArtifact(
        interchange_artifact_id="interchange-artifact:julia-json:reference-regression:v1",
        logical_data_ref=logical_ref,
        format=InterchangeFormat.json,
        uri="core-ref://interchange/julia/reference-regression.json",
        content_sha256="a" * 64,
        data_schema=schema,
        media_type="application/json",
        size_bytes=128,
        producer_runtime_ref=REFERENCE_R_RUNTIME,
        producer_runtime_version=REFERENCE_R_VERSION,
        source_artifact_refs=[source.interchange_artifact_id],
        provenance={
            "consumer_runtime": REFERENCE_JULIA_RUNTIME,
            "direct_transfer_without_conversion": True,
        },
    )

    verification = DataInterchangeVerification(
        verification_id="interchange-verification:r-to-julia:reference-regression:v1",
        source_artifact_ref=source.interchange_artifact_id,
        target_artifact_ref=target.interchange_artifact_id,
        status=VerificationStatus.passed,
        source_schema_fingerprint_sha256=schema.fingerprint(),
        target_schema_fingerprint_sha256=schema.fingerprint(),
        row_count_match=True,
        column_count_match=True,
        type_compatibility_passed=True,
        null_semantics_preserved=True,
        categorical_semantics_preserved=True,
        numerical_tolerance=0.0,
        notes=[
            "Reference proof uses JSON because both currently registered runtime profiles declare JSON interchange.",
            "Arrow IPC and Parquet are contract-supported formats but are not claimed as native provider capabilities in this release.",
        ],
    )

    transfer = DataInterchangeTransfer(
        transfer_id="interchange-transfer:r-to-julia:reference-regression:v1",
        source_artifact=source,
        target_artifact=target,
        source_runtime_ref=REFERENCE_R_RUNTIME,
        target_runtime_ref=REFERENCE_JULIA_RUNTIME,
        verification=verification,
        status=InterchangeStatus.completed,
        completed_at=datetime(2026, 9, 25, tzinfo=timezone.utc),
        provenance={
            "core_selected_format": False,
            "format_selected_by": "reference-contract",
        },
    )

    return RuntimeDataInterchangeBundle(
        bundle_id="runtime-data-interchange-bundle:reference-r-julia:v1",
        profiles=profiles,
        transfers=[transfer],
        source_object_refs=[
            "stat-package:reference-regression:v1",
            "scientific-registry-package:reference-regression:v1",
        ],
        metadata={
            "cross_runtime": True,
            "payload_execution_owner": "runtime-providers-or-workspace",
        },
    )


def contract_document() -> dict[str, Any]:
    reference = reference_runtime_data_interchange_bundle()

    negotiation = negotiate_interchange(
        DataInterchangeNegotiationRequest(
            source_profile=reference.profiles[0],
            target_profile=reference.profiles[1],
            required_shape=DataShapeKind.table,
            required_types=[CanonicalScalarType.float64],
            preferred_formats=[
                InterchangeFormat.arrow_ipc_stream,
                InterchangeFormat.parquet,
                InterchangeFormat.json,
            ],
        )
    )

    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "depends_on": [
            R_RUNTIME_CONTRACT,
            RUNTIME_OBJECT_CONTRACT,
            RUNTIME_ADAPTER_CONTRACT,
            COMPUTATIONAL_JOB_CONTRACT,
            ENVIRONMENT_PROVENANCE_CONTRACT,
            SCIENTIFIC_REGISTRY_CONTRACT,
        ],
        "object_types": [
            "DataFieldSchema",
            "DataInterchangeSchema",
            "RuntimeTypeMapping",
            "RuntimeInterchangeProfile",
            "DataInterchangeArtifact",
            "DataInterchangeNegotiationRequest",
            "DataInterchangeNegotiationResult",
            "DataInterchangeConversionSpec",
            "DataInterchangeVerification",
            "DataInterchangeTransfer",
            "RuntimeDataInterchangeBundle",
        ],
        "formats": [item.value for item in InterchangeFormat],
        "capabilities": {
            "canonical_data_types": True,
            "shape_aware_schemas": True,
            "runtime_type_mappings": True,
            "runtime_interchange_profiles": True,
            "format_candidate_discovery": True,
            "loss_policy": True,
            "conversion_specs": True,
            "schema_and_content_fingerprints": True,
            "transfer_verification": True,
            "scientific_artifact_bridge": True,
            "json_csv_interchange": True,
            "arrow_parquet_contract_support": True,
        },
        "integration": {
            "r_runtime_profile": True,
            "julia_runtime_profile": True,
            "statistical_objects_sourceable": True,
            "scientific_registry_bridge": True,
            "workspace_or_runtime_executes_conversion": True,
            "core_executes_conversion": False,
        },
        "boundaries": {
            "core_autonomously_selects_format": False,
            "core_executes_data_conversion": False,
            "core_claims_semantic_equivalence_without_verification": False,
            "core_claims_arrow_parquet_provider_support_without_registration": False,
            "core_certifies_scientific_validity": False,
            "core_owns_interchange_contracts_lineage_and_verification_objects": True,
        },
        "reference": {
            "bundle_id": reference.bundle_id,
            "transfer_id": reference.transfers[0].transfer_id,
            "negotiation_candidates": [
                item.value for item in negotiation.candidate_formats
            ],
            "bundle_fingerprint_sha256": reference.fingerprint(),
        },
    }
