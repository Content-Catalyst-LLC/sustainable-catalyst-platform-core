from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256

CORE_RELEASE = "3.38.0"
CONTRACT_VERSION = "sc.core.scientific-result-artifact-registry.v1"

STATISTICAL_ANALYSIS_CONTRACT = "sc.core.statistical-analysis-object.v1"
AI_RESEARCH_OBJECT_CONTRACT = "sc.core.ai-research-object-system.v1"
COMPUTATIONAL_JOB_CONTRACT = "sc.core.computational-job.v1"
ENVIRONMENT_PROVENANCE_CONTRACT = "sc.core.execution-environment-provenance.v1"
RUNTIME_OBJECT_CONTRACT = "sc.core.computational-runtime-object.v1"


class ScientificResultKind(str, Enum):
    statistical_estimate = "statistical-estimate"
    hypothesis_test = "hypothesis-test"
    effect_size = "effect-size"
    model_fit = "model-fit"
    diagnostic = "diagnostic"
    matrix = "matrix"
    simulation = "simulation"
    forecast = "forecast"
    calibration = "calibration"
    drift = "drift"
    robustness = "robustness"
    causal_estimate = "causal-estimate"
    optimization = "optimization"
    measurement = "measurement"
    derived_metric = "derived-metric"
    finding = "finding"
    other = "other"


class ScientificArtifactKind(str, Enum):
    table = "table"
    figure = "figure"
    chart = "chart"
    matrix = "matrix"
    dataset = "dataset"
    model = "model"
    checkpoint = "checkpoint"
    notebook = "notebook"
    script = "script"
    report = "report"
    publication = "publication"
    package = "package"
    image = "image"
    geospatial = "geospatial"
    binary = "binary"
    json = "json"
    csv = "csv"
    parquet = "parquet"
    other = "other"


class ScientificRegistryState(str, Enum):
    declared = "declared"
    registered = "registered"
    superseded = "superseded"
    archived = "archived"
    invalidated = "invalidated"


class ScientificRelationType(str, Enum):
    derived_from = "derived-from"
    produced_by = "produced-by"
    visualizes = "visualizes"
    tabulates = "tabulates"
    summarizes = "summarizes"
    supports = "supports"
    contradicts = "contradicts"
    validates = "validates"
    reproduces = "reproduces"
    generated_from = "generated-from"
    depends_on = "depends-on"
    source_for = "source-for"
    packages = "packages"
    other = "other"


class ScientificResultRef(BaseModel):
    result_id: str = Field(min_length=2, max_length=500)
    result_kind: ScientificResultKind
    source_contract: str = Field(min_length=2, max_length=300)
    source_object_ref: str = Field(min_length=2, max_length=1000)
    fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    title: str | None = Field(default=None, max_length=500)
    summary: str | None = Field(default=None, max_length=10000)
    unit: str | None = Field(default=None, max_length=200)
    state: ScientificRegistryState = ScientificRegistryState.registered
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("state", None)
        return canonical_sha256(payload)


class ScientificArtifactRef(BaseModel):
    artifact_id: str = Field(min_length=2, max_length=500)
    artifact_kind: ScientificArtifactKind
    uri: str = Field(min_length=2, max_length=4000)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    media_type: str | None = Field(default=None, max_length=300)
    size_bytes: int | None = Field(default=None, ge=0)
    source_contract: str | None = Field(default=None, max_length=300)
    source_object_ref: str | None = Field(default=None, max_length=1000)
    state: ScientificRegistryState = ScientificRegistryState.registered
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("state", None)
        return canonical_sha256(payload)


class ScientificRegistryRelation(BaseModel):
    relation_id: str = Field(min_length=2, max_length=500)
    source_ref: str = Field(min_length=2, max_length=1000)
    target_ref: str = Field(min_length=2, max_length=1000)
    relation_type: ScientificRelationType
    evidence_refs: list[str] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_relation(self):
        if self.source_ref == self.target_ref:
            raise ValueError("scientific registry relation cannot be self-referential")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ScientificResultArtifactRegistry(BaseModel):
    registry_id: str = Field(min_length=2, max_length=500)
    results: list[ScientificResultRef] = Field(default_factory=list)
    artifacts: list[ScientificArtifactRef] = Field(default_factory=list)
    relations: list[ScientificRegistryRelation] = Field(default_factory=list)
    source_release_refs: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_registry(self):
        result_ids = [item.result_id for item in self.results]
        artifact_ids = [item.artifact_id for item in self.artifacts]
        relation_ids = [item.relation_id for item in self.relations]

        if len(result_ids) != len(set(result_ids)):
            raise ValueError("scientific result ids must be unique")
        if len(artifact_ids) != len(set(artifact_ids)):
            raise ValueError("scientific artifact ids must be unique")
        if len(relation_ids) != len(set(relation_ids)):
            raise ValueError("scientific relation ids must be unique")

        known = set(result_ids) | set(artifact_ids)
        for relation in self.relations:
            if relation.source_ref not in known:
                raise ValueError("relation source is outside scientific registry")
            if relation.target_ref not in known:
                raise ValueError("relation target is outside scientific registry")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256({
            "registry_id": self.registry_id,
            "result_fingerprints": sorted(item.fingerprint() for item in self.results),
            "artifact_fingerprints": sorted(item.fingerprint() for item in self.artifacts),
            "relation_fingerprints": sorted(item.fingerprint() for item in self.relations),
            "source_release_refs": sorted(self.source_release_refs),
            "metadata": self.metadata,
        })


class ScientificRegistryQuery(BaseModel):
    result_kinds: list[ScientificResultKind] = Field(default_factory=list)
    artifact_kinds: list[ScientificArtifactKind] = Field(default_factory=list)
    source_contracts: list[str] = Field(default_factory=list)
    source_object_refs: list[str] = Field(default_factory=list)
    state: ScientificRegistryState | None = None


class ScientificRegistryQueryResult(BaseModel):
    result_refs: list[str] = Field(default_factory=list)
    artifact_refs: list[str] = Field(default_factory=list)
    relation_refs: list[str] = Field(default_factory=list)
    registry_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ScientificRegistrySnapshot(BaseModel):
    snapshot_id: str = Field(min_length=2, max_length=500)
    registry_ref: str = Field(min_length=2, max_length=500)
    registry_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    selected_result_refs: list[str] = Field(default_factory=list)
    selected_artifact_refs: list[str] = Field(default_factory=list)
    selected_relation_refs: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("created_at", None)
        return canonical_sha256(payload)


class ScientificRegistryPackage(BaseModel):
    package_id: str = Field(min_length=2, max_length=500)
    registry: ScientificResultArtifactRegistry
    snapshot: ScientificRegistrySnapshot

    @model_validator(mode="after")
    def validate_package(self):
        if self.snapshot.registry_ref != self.registry.registry_id:
            raise ValueError("snapshot registry_ref does not match registry")
        if self.snapshot.registry_fingerprint_sha256 != self.registry.fingerprint():
            raise ValueError("snapshot registry fingerprint mismatch")

        result_ids = {item.result_id for item in self.registry.results}
        artifact_ids = {item.artifact_id for item in self.registry.artifacts}
        relation_ids = {item.relation_id for item in self.registry.relations}

        if not set(self.snapshot.selected_result_refs).issubset(result_ids):
            raise ValueError("snapshot references result outside registry")
        if not set(self.snapshot.selected_artifact_refs).issubset(artifact_ids):
            raise ValueError("snapshot references artifact outside registry")
        if not set(self.snapshot.selected_relation_refs).issubset(relation_ids):
            raise ValueError("snapshot references relation outside registry")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256({
            "package_id": self.package_id,
            "registry_fingerprint_sha256": self.registry.fingerprint(),
            "snapshot_fingerprint_sha256": self.snapshot.fingerprint(),
        })


def query_registry(
    registry: ScientificResultArtifactRegistry,
    query: ScientificRegistryQuery,
) -> ScientificRegistryQueryResult:
    result_kind_filter = set(query.result_kinds)
    artifact_kind_filter = set(query.artifact_kinds)
    source_contract_filter = set(query.source_contracts)
    source_object_filter = set(query.source_object_refs)

    result_refs: list[str] = []
    for item in registry.results:
        if result_kind_filter and item.result_kind not in result_kind_filter:
            continue
        if source_contract_filter and item.source_contract not in source_contract_filter:
            continue
        if source_object_filter and item.source_object_ref not in source_object_filter:
            continue
        if query.state is not None and item.state != query.state:
            continue
        result_refs.append(item.result_id)

    artifact_refs: list[str] = []
    for item in registry.artifacts:
        if artifact_kind_filter and item.artifact_kind not in artifact_kind_filter:
            continue
        if source_contract_filter and item.source_contract not in source_contract_filter:
            continue
        if source_object_filter and item.source_object_ref not in source_object_filter:
            continue
        if query.state is not None and item.state != query.state:
            continue
        artifact_refs.append(item.artifact_id)

    selected = set(result_refs) | set(artifact_refs)
    relation_refs = [
        rel.relation_id
        for rel in registry.relations
        if rel.source_ref in selected or rel.target_ref in selected
    ]

    return ScientificRegistryQueryResult(
        result_refs=sorted(result_refs),
        artifact_refs=sorted(artifact_refs),
        relation_refs=sorted(set(relation_refs)),
        registry_fingerprint_sha256=registry.fingerprint(),
    )


def register_statistical_analysis_package(
    *,
    analysis_package: dict[str, Any],
) -> ScientificResultArtifactRegistry:
    plan = analysis_package.get("plan", {})
    results = analysis_package.get("results", [])
    package_id = str(analysis_package.get("package_id", "statistical-package:unknown"))

    scientific_results: list[ScientificResultRef] = []
    scientific_artifacts: list[ScientificArtifactRef] = []
    relations: list[ScientificRegistryRelation] = []

    for result in results:
        analysis_result_id = str(result["analysis_result_id"])

        for estimate in result.get("estimates", []):
            rid = f"scientific-result:{estimate['estimate_id']}"
            scientific_results.append(
                ScientificResultRef(
                    result_id=rid,
                    result_kind=ScientificResultKind.statistical_estimate,
                    source_contract=STATISTICAL_ANALYSIS_CONTRACT,
                    source_object_ref=str(estimate["estimate_id"]),
                    fingerprint_sha256=canonical_sha256(estimate),
                    title=f"Estimate: {estimate['term']}",
                    unit=estimate.get("unit"),
                    metadata={
                        "analysis_result_ref": analysis_result_id,
                        "analysis_plan_ref": result["analysis_plan_ref"],
                    },
                )
            )

        for test in result.get("hypothesis_tests", []):
            rid = f"scientific-result:{test['test_result_id']}"
            scientific_results.append(
                ScientificResultRef(
                    result_id=rid,
                    result_kind=ScientificResultKind.hypothesis_test,
                    source_contract=STATISTICAL_ANALYSIS_CONTRACT,
                    source_object_ref=str(test["test_result_id"]),
                    fingerprint_sha256=canonical_sha256(test),
                    title=str(test["test_name"]),
                    metadata={
                        "analysis_result_ref": analysis_result_id,
                        "p_value": test.get("p_value"),
                    },
                )
            )

        for effect in result.get("effect_sizes", []):
            rid = f"scientific-result:{effect['effect_size_id']}"
            scientific_results.append(
                ScientificResultRef(
                    result_id=rid,
                    result_kind=ScientificResultKind.effect_size,
                    source_contract=STATISTICAL_ANALYSIS_CONTRACT,
                    source_object_ref=str(effect["effect_size_id"]),
                    fingerprint_sha256=canonical_sha256(effect),
                    title=f"Effect size: {effect['measure']}",
                    metadata={"analysis_result_ref": analysis_result_id},
                )
            )

        for fit in result.get("fit_statistics", []):
            rid = f"scientific-result:{fit['fit_statistic_id']}"
            scientific_results.append(
                ScientificResultRef(
                    result_id=rid,
                    result_kind=ScientificResultKind.model_fit,
                    source_contract=STATISTICAL_ANALYSIS_CONTRACT,
                    source_object_ref=str(fit["fit_statistic_id"]),
                    fingerprint_sha256=canonical_sha256(fit),
                    title=f"Model fit: {fit['name']}",
                    metadata={"analysis_result_ref": analysis_result_id},
                )
            )

        for diagnostic in result.get("diagnostics", []):
            rid = f"scientific-result:{diagnostic['diagnostic_id']}"
            scientific_results.append(
                ScientificResultRef(
                    result_id=rid,
                    result_kind=ScientificResultKind.diagnostic,
                    source_contract=STATISTICAL_ANALYSIS_CONTRACT,
                    source_object_ref=str(diagnostic["diagnostic_id"]),
                    fingerprint_sha256=canonical_sha256(diagnostic),
                    title=f"Diagnostic: {diagnostic['name']}",
                    metadata={"analysis_result_ref": analysis_result_id},
                )
            )

        for matrix in result.get("matrix_results", []):
            rid = f"scientific-result:{matrix['matrix_result_id']}"
            scientific_results.append(
                ScientificResultRef(
                    result_id=rid,
                    result_kind=ScientificResultKind.matrix,
                    source_contract=STATISTICAL_ANALYSIS_CONTRACT,
                    source_object_ref=str(matrix["matrix_result_id"]),
                    fingerprint_sha256=canonical_sha256(matrix),
                    title=str(matrix["name"]),
                    metadata={"analysis_result_ref": analysis_result_id},
                )
            )

        for artifact_ref in result.get("artifact_refs", []):
            aid = f"scientific-artifact:{artifact_ref}"
            scientific_artifacts.append(
                ScientificArtifactRef(
                    artifact_id=aid,
                    artifact_kind=ScientificArtifactKind.other,
                    uri=f"core-ref://{artifact_ref}",
                    content_sha256=canonical_sha256({
                        "artifact_ref": artifact_ref,
                        "analysis_result_ref": analysis_result_id,
                    }),
                    source_contract=STATISTICAL_ANALYSIS_CONTRACT,
                    source_object_ref=str(artifact_ref),
                    metadata={"analysis_result_ref": analysis_result_id},
                )
            )

    package_artifact_id = f"scientific-artifact:{package_id}"
    scientific_artifacts.append(
        ScientificArtifactRef(
            artifact_id=package_artifact_id,
            artifact_kind=ScientificArtifactKind.package,
            uri=f"core-ref://{package_id}",
            content_sha256=canonical_sha256(analysis_package),
            source_contract=STATISTICAL_ANALYSIS_CONTRACT,
            source_object_ref=package_id,
            metadata={
                "analysis_plan_ref": plan.get("analysis_plan_id"),
                "portable_package": True,
            },
        )
    )

    for result_ref in scientific_results:
        relations.append(
            ScientificRegistryRelation(
                relation_id=f"relation:{result_ref.result_id}:packaged-by:{package_artifact_id}",
                source_ref=result_ref.result_id,
                target_ref=package_artifact_id,
                relation_type=ScientificRelationType.packages,
            )
        )

    return ScientificResultArtifactRegistry(
        registry_id=f"scientific-registry:{package_id}",
        results=scientific_results,
        artifacts=scientific_artifacts,
        relations=relations,
        source_release_refs=["v3.37.0", "v3.38.0"],
        metadata={
            "source_statistical_package_id": package_id,
            "source_payload_duplicated": False,
            "registry_mode": "reference-and-fingerprint",
        },
    )


def reference_scientific_registry_package() -> ScientificRegistryPackage:
    from .statistical_analysis_objects import reference_statistical_analysis_package

    statistical_package = reference_statistical_analysis_package()
    statistical_payload = statistical_package.model_dump(mode="json", exclude_none=True)

    registry = register_statistical_analysis_package(
        analysis_package=statistical_payload,
    )

    snapshot = ScientificRegistrySnapshot(
        snapshot_id="scientific-registry-snapshot:reference-regression:v1",
        registry_ref=registry.registry_id,
        registry_fingerprint_sha256=registry.fingerprint(),
        selected_result_refs=[item.result_id for item in registry.results],
        selected_artifact_refs=[item.artifact_id for item in registry.artifacts],
        selected_relation_refs=[item.relation_id for item in registry.relations],
        provenance={
            "source_release": "v3.38.0",
            "source_statistical_contract": STATISTICAL_ANALYSIS_CONTRACT,
        },
    )

    return ScientificRegistryPackage(
        package_id="scientific-registry-package:reference-regression:v1",
        registry=registry,
        snapshot=snapshot,
    )


def contract_document() -> dict[str, Any]:
    reference = reference_scientific_registry_package()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "depends_on": [
            STATISTICAL_ANALYSIS_CONTRACT,
            AI_RESEARCH_OBJECT_CONTRACT,
            COMPUTATIONAL_JOB_CONTRACT,
            ENVIRONMENT_PROVENANCE_CONTRACT,
            RUNTIME_OBJECT_CONTRACT,
        ],
        "object_types": [
            "ScientificResultRef",
            "ScientificArtifactRef",
            "ScientificRegistryRelation",
            "ScientificResultArtifactRegistry",
            "ScientificRegistryQuery",
            "ScientificRegistryQueryResult",
            "ScientificRegistrySnapshot",
            "ScientificRegistryPackage",
        ],
        "capabilities": {
            "cross_domain_result_identity": True,
            "content_addressed_artifacts": True,
            "typed_result_artifact_relations": True,
            "statistical_result_registration": True,
            "registry_queries": True,
            "registry_snapshots": True,
            "portable_registry_packages": True,
            "source_contract_traceability": True,
            "source_payload_reference_mode": True,
        },
        "integration": {
            "statistical_analysis_objects_registerable": True,
            "ai_research_objects_registerable": True,
            "runtime_artifacts_referenceable": True,
            "knowledge_library_artifacts_referenceable": True,
            "research_lab_artifacts_referenceable": True,
            "core_duplicates_source_payloads": False,
        },
        "boundaries": {
            "core_executes_scientific_methods": False,
            "core_modifies_source_artifacts": False,
            "core_certifies_scientific_validity": False,
            "core_interprets_results_as_truth": False,
            "core_owns_registry_identity_lineage_and_exchange": True,
        },
        "reference": {
            "registry_id": reference.registry.registry_id,
            "snapshot_id": reference.snapshot.snapshot_id,
            "package_id": reference.package_id,
            "result_count": len(reference.registry.results),
            "artifact_count": len(reference.registry.artifacts),
            "relation_count": len(reference.registry.relations),
            "package_fingerprint_sha256": reference.fingerprint(),
        },
    }
