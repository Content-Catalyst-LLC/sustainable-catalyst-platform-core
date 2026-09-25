from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256

CORE_RELEASE = "3.35.0"
CONTRACT_VERSION = "sc.core.ai-research-object-system.v1"

AI_MODEL_CONTRACT_VERSION = "sc.core.ai-model.v1"
AI_TRAINING_LINEAGE_CONTRACT_VERSION = "sc.core.ai-training-lineage.v1"
AI_INFERENCE_CONTRACT_VERSION = "sc.core.ai-inference-provenance.v1"
PROMPT_CONTEXT_CONTRACT_VERSION = "sc.core.prompt-context-retrieval.v1"
AI_EVALUATION_CONTRACT_VERSION = "sc.core.ai-evaluation-benchmark.v1"
AI_EXPERIMENT_CONTRACT_VERSION = "sc.core.ai-experiment-reproducibility.v1"
AI_ERROR_ROBUSTNESS_CONTRACT_VERSION = "sc.core.ai-error-robustness.v1"
AI_CALIBRATION_DRIFT_RISK_CONTRACT_VERSION = "sc.core.ai-calibration-drift-risk.v1"
COMPUTATIONAL_RUNTIME_OBJECT_CONTRACT_VERSION = "sc.core.computational-runtime-object.v1"
COMPUTATIONAL_JOB_CONTRACT_VERSION = "sc.core.computational-job.v1"
ENVIRONMENT_PROVENANCE_CONTRACT_VERSION = "sc.core.execution-environment-provenance.v1"


class AIResearchObjectKind(str, Enum):
    ai_model = "ai-model"
    ai_model_version = "ai-model-version"
    dataset = "dataset"
    dataset_version = "dataset-version"
    feature_set = "feature-set"
    training_lineage = "training-lineage"
    inference_run = "inference-run"
    ai_artifact = "ai-artifact"
    prompt = "prompt"
    prompt_version = "prompt-version"
    retrieval_query = "retrieval-query"
    retrieval_result_set = "retrieval-result-set"
    context_assembly = "context-assembly"
    benchmark = "benchmark"
    evaluation_case = "evaluation-case"
    evaluation_run = "evaluation-run"
    benchmark_result = "benchmark-result"
    experiment = "experiment"
    experiment_run_binding = "experiment-run-binding"
    reproducibility_package = "reproducibility-package"
    reproduction_attempt = "reproduction-attempt"
    failure_taxonomy = "failure-taxonomy"
    error_observation = "error-observation"
    evaluation_slice = "evaluation-slice"
    robustness_test = "robustness-test"
    robustness_run = "robustness-run"
    error_analysis_report = "error-analysis-report"
    calibration_assessment = "calibration-assessment"
    monitoring_window = "monitoring-window"
    drift_signal = "drift-signal"
    drift_observation = "drift-observation"
    risk_indicator = "risk-indicator"
    risk_observation = "risk-observation"
    monitoring_policy = "monitoring-policy"
    monitoring_snapshot = "monitoring-snapshot"
    computational_job = "computational-job"
    runtime_environment = "runtime-environment"
    runtime_artifact = "runtime-artifact"
    evidence = "evidence"
    claim = "claim"
    finding = "finding"
    other = "other"


class AIResearchRelationshipType(str, Enum):
    contains = "contains"
    references = "references"
    derived_from = "derived-from"
    produced_by = "produced-by"
    consumes = "consumes"
    trained_on = "trained-on"
    uses_feature_set = "uses-feature-set"
    uses_prompt = "uses-prompt"
    uses_context = "uses-context"
    generated_by = "generated-by"
    evaluated_by = "evaluated-by"
    evaluates = "evaluates"
    benchmarked_by = "benchmarked-by"
    includes = "includes"
    reproduces = "reproduces"
    reproduction_of = "reproduction-of"
    reports_error = "reports-error"
    observed_in = "observed-in"
    robustness_tested_by = "robustness-tested-by"
    calibrated_by = "calibrated-by"
    drift_observed_by = "drift-observed-by"
    risk_observed_by = "risk-observed-by"
    monitored_by = "monitored-by"
    evidence_for = "evidence-for"
    supports = "supports"
    contradicts = "contradicts"
    executed_as = "executed-as"
    executed_in = "executed-in"
    emitted = "emitted"
    other = "other"


class AIResearchLifecycleState(str, Enum):
    declared = "declared"
    active = "active"
    superseded = "superseded"
    archived = "archived"
    invalidated = "invalidated"


class LineageDirection(str, Enum):
    upstream = "upstream"
    downstream = "downstream"
    both = "both"


class AIResearchContractBinding(BaseModel):
    binding_id: str = Field(min_length=2, max_length=300)
    contract: str = Field(min_length=2, max_length=300)
    introduced_release: str = Field(min_length=1, max_length=64)
    object_kinds: list[AIResearchObjectKind] = Field(default_factory=list)
    source_module: str | None = Field(default=None, max_length=300)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class AIResearchSystemManifest(BaseModel):
    manifest_id: str = Field(min_length=2, max_length=300)
    system_contract: str = Field(default=CONTRACT_VERSION)
    core_release: str = Field(default=CORE_RELEASE)
    contract_bindings: list[AIResearchContractBinding] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_bindings(self):
        ids = [item.binding_id for item in self.contract_bindings]
        contracts = [item.contract for item in self.contract_bindings]
        if len(ids) != len(set(ids)):
            raise ValueError("contract binding ids must be unique")
        if len(contracts) != len(set(contracts)):
            raise ValueError("contract bindings must use unique contracts")
        if self.system_contract != CONTRACT_VERSION:
            raise ValueError("system_contract must match current unified contract")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("created_at", None)
        return canonical_sha256(payload)


class AIResearchObjectRef(BaseModel):
    object_id: str = Field(min_length=2, max_length=500)
    object_kind: AIResearchObjectKind
    contract: str = Field(min_length=2, max_length=300)
    object_version: str | None = Field(default=None, max_length=200)
    fingerprint_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    product_owner: str | None = Field(default=None, max_length=200)
    payload_ref: str | None = Field(default=None, max_length=2000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class AIResearchObjectEnvelope(BaseModel):
    object_ref: AIResearchObjectRef
    title: str | None = Field(default=None, max_length=500)
    lifecycle_state: AIResearchLifecycleState = AIResearchLifecycleState.active
    immutable_source_object: bool = True
    created_at: datetime | None = None
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("registered_at", None)
        payload.pop("lifecycle_state", None)
        return canonical_sha256(payload)


class AIResearchRelationship(BaseModel):
    relationship_id: str = Field(min_length=2, max_length=500)
    source_object_ref: str = Field(min_length=2, max_length=500)
    target_object_ref: str = Field(min_length=2, max_length=500)
    relationship_type: AIResearchRelationshipType
    contract: str = Field(default=CONTRACT_VERSION, max_length=300)
    evidence_refs: list[str] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    asserted_by: str | None = Field(default=None, max_length=300)
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_relationship(self):
        if self.source_object_ref == self.target_object_ref:
            raise ValueError("relationship cannot be self-referential")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class AIResearchObjectRegistry(BaseModel):
    registry_id: str = Field(min_length=2, max_length=300)
    objects: list[AIResearchObjectEnvelope] = Field(default_factory=list)
    contract_manifest_ref: str | None = Field(default=None, max_length=300)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_registry(self):
        ids = [item.object_ref.object_id for item in self.objects]
        if len(ids) != len(set(ids)):
            raise ValueError("AI research object ids must be unique in registry")
        return self

    def object_index(self) -> dict[str, AIResearchObjectEnvelope]:
        return {item.object_ref.object_id: item for item in self.objects}

    def fingerprint(self) -> str:
        return canonical_sha256({
            "registry_id": self.registry_id,
            "contract_manifest_ref": self.contract_manifest_ref,
            "object_fingerprints": sorted(item.fingerprint() for item in self.objects),
            "metadata": self.metadata,
        })


class AIResearchRelationshipGraph(BaseModel):
    graph_id: str = Field(min_length=2, max_length=300)
    registry_ref: str = Field(min_length=2, max_length=300)
    object_ids: list[str] = Field(default_factory=list)
    relationships: list[AIResearchRelationship] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_graph(self):
        if len(self.object_ids) != len(set(self.object_ids)):
            raise ValueError("graph object ids must be unique")

        rel_ids = [item.relationship_id for item in self.relationships]
        if len(rel_ids) != len(set(rel_ids)):
            raise ValueError("relationship ids must be unique")

        known = set(self.object_ids)
        for edge in self.relationships:
            if edge.source_object_ref not in known:
                raise ValueError("relationship source is not declared in graph")
            if edge.target_object_ref not in known:
                raise ValueError("relationship target is not declared in graph")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256({
            "graph_id": self.graph_id,
            "registry_ref": self.registry_ref,
            "object_ids": sorted(self.object_ids),
            "relationship_fingerprints": sorted(
                item.fingerprint() for item in self.relationships
            ),
            "metadata": self.metadata,
        })


class AIResearchLineageQuery(BaseModel):
    start_object_ref: str = Field(min_length=2, max_length=500)
    direction: LineageDirection = LineageDirection.upstream
    relationship_types: list[AIResearchRelationshipType] = Field(default_factory=list)
    max_depth: int = Field(default=6, ge=0, le=100)
    include_start: bool = True


class AIResearchLineagePath(BaseModel):
    start_object_ref: str
    direction: LineageDirection
    object_refs: list[str] = Field(default_factory=list)
    relationship_refs: list[str] = Field(default_factory=list)
    depths: dict[str, int] = Field(default_factory=dict)
    truncated: bool = False

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class AIResearchSnapshot(BaseModel):
    snapshot_id: str = Field(min_length=2, max_length=300)
    manifest_ref: str = Field(min_length=2, max_length=300)
    registry_ref: str = Field(min_length=2, max_length=300)
    graph_ref: str = Field(min_length=2, max_length=300)
    manifest_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    registry_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    graph_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_release_refs: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("created_at", None)
        return canonical_sha256(payload)


class AIResearchPackageManifest(BaseModel):
    package_id: str = Field(min_length=2, max_length=300)
    snapshot_ref: str = Field(min_length=2, max_length=300)
    selected_object_refs: list[str] = Field(default_factory=list)
    selected_relationship_refs: list[str] = Field(default_factory=list)
    root_object_refs: list[str] = Field(default_factory=list)
    purpose: str | None = Field(default=None, max_length=10000)
    package_format_version: str = Field(default="1.0.0", min_length=1, max_length=100)
    content_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_package(self):
        if not self.selected_object_refs:
            raise ValueError("AI research package requires selected objects")
        unknown_roots = [
            ref for ref in self.root_object_refs if ref not in self.selected_object_refs
        ]
        if unknown_roots:
            raise ValueError("package root objects must be selected objects")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class UnifiedAIResearchObjectBundle(BaseModel):
    manifest: AIResearchSystemManifest
    registry: AIResearchObjectRegistry
    graph: AIResearchRelationshipGraph
    snapshot: AIResearchSnapshot
    packages: list[AIResearchPackageManifest] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_bundle(self):
        if self.registry.contract_manifest_ref != self.manifest.manifest_id:
            raise ValueError("registry must reference unified manifest")

        if self.graph.registry_ref != self.registry.registry_id:
            raise ValueError("graph must reference registry")

        registry_ids = set(self.registry.object_index())
        graph_ids = set(self.graph.object_ids)
        if graph_ids != registry_ids:
            raise ValueError("graph object set must exactly match registry object set")

        expected_contract_by_kind: dict[AIResearchObjectKind, str] = {}
        for binding in self.manifest.contract_bindings:
            for kind in binding.object_kinds:
                if kind in expected_contract_by_kind:
                    raise ValueError("object kind is bound by multiple source contracts")
                expected_contract_by_kind[kind] = binding.contract

        for envelope in self.registry.objects:
            ref = envelope.object_ref
            expected_contract = expected_contract_by_kind.get(ref.object_kind)
            if expected_contract and ref.contract != expected_contract:
                raise ValueError(
                    "registered object contract does not match unified manifest binding"
                )

        if self.snapshot.manifest_ref != self.manifest.manifest_id:
            raise ValueError("snapshot manifest_ref mismatch")
        if self.snapshot.registry_ref != self.registry.registry_id:
            raise ValueError("snapshot registry_ref mismatch")
        if self.snapshot.graph_ref != self.graph.graph_id:
            raise ValueError("snapshot graph_ref mismatch")
        if self.snapshot.manifest_fingerprint_sha256 != self.manifest.fingerprint():
            raise ValueError("snapshot manifest fingerprint mismatch")
        if self.snapshot.registry_fingerprint_sha256 != self.registry.fingerprint():
            raise ValueError("snapshot registry fingerprint mismatch")
        if self.snapshot.graph_fingerprint_sha256 != self.graph.fingerprint():
            raise ValueError("snapshot graph fingerprint mismatch")

        relationship_ids = {
            item.relationship_id for item in self.graph.relationships
        }
        for edge in self.graph.relationships:
            if edge.contract != CONTRACT_VERSION:
                raise ValueError("relationship contract must use unified AI research contract")

        for package in self.packages:
            if package.snapshot_ref != self.snapshot.snapshot_id:
                raise ValueError("package snapshot_ref must match bundle snapshot")
            missing_objects = [
                ref for ref in package.selected_object_refs if ref not in registry_ids
            ]
            if missing_objects:
                raise ValueError("package references object outside registry")
            missing_edges = [
                ref
                for ref in package.selected_relationship_refs
                if ref not in relationship_ids
            ]
            if missing_edges:
                raise ValueError("package references relationship outside graph")

        return self

    def fingerprint(self) -> str:
        return canonical_sha256({
            "manifest_fingerprint_sha256": self.manifest.fingerprint(),
            "registry_fingerprint_sha256": self.registry.fingerprint(),
            "graph_fingerprint_sha256": self.graph.fingerprint(),
            "snapshot_fingerprint_sha256": self.snapshot.fingerprint(),
            "package_fingerprints": sorted(
                item.fingerprint() for item in self.packages
            ),
        })


def trace_lineage(
    graph: AIResearchRelationshipGraph,
    query: AIResearchLineageQuery,
) -> AIResearchLineagePath:
    known = set(graph.object_ids)
    if query.start_object_ref not in known:
        raise ValueError("lineage start object is not present in graph")

    allowed = set(query.relationship_types)
    use_filter = bool(allowed)

    outgoing: dict[str, list[AIResearchRelationship]] = {}
    incoming: dict[str, list[AIResearchRelationship]] = {}
    for edge in graph.relationships:
        outgoing.setdefault(edge.source_object_ref, []).append(edge)
        incoming.setdefault(edge.target_object_ref, []).append(edge)

    queue: deque[tuple[str, int]] = deque([(query.start_object_ref, 0)])
    seen = {query.start_object_ref}
    object_refs: list[str] = [query.start_object_ref] if query.include_start else []
    relationship_refs: list[str] = []
    depths = {query.start_object_ref: 0} if query.include_start else {}
    truncated = False

    while queue:
        current, depth = queue.popleft()
        if depth >= query.max_depth:
            candidates = []
            if query.direction in (LineageDirection.upstream, LineageDirection.both):
                candidates.extend(outgoing.get(current, []))
            if query.direction in (LineageDirection.downstream, LineageDirection.both):
                candidates.extend(incoming.get(current, []))
            if any((not use_filter or edge.relationship_type in allowed) for edge in candidates):
                truncated = True
            continue

        candidates: list[tuple[AIResearchRelationship, str]] = []

        # Graph convention: source objects point to the objects they depend on.
        # Upstream therefore follows outgoing edges to dependencies; downstream
        # follows incoming edges to dependents.
        if query.direction in (LineageDirection.upstream, LineageDirection.both):
            for edge in outgoing.get(current, []):
                candidates.append((edge, edge.target_object_ref))

        if query.direction in (LineageDirection.downstream, LineageDirection.both):
            for edge in incoming.get(current, []):
                candidates.append((edge, edge.source_object_ref))

        candidates.sort(key=lambda pair: (pair[0].relationship_id, pair[1]))

        for edge, neighbor in candidates:
            if use_filter and edge.relationship_type not in allowed:
                continue
            if edge.relationship_id not in relationship_refs:
                relationship_refs.append(edge.relationship_id)
            if neighbor in seen:
                continue
            seen.add(neighbor)
            object_refs.append(neighbor)
            depths[neighbor] = depth + 1
            queue.append((neighbor, depth + 1))

    return AIResearchLineagePath(
        start_object_ref=query.start_object_ref,
        direction=query.direction,
        object_refs=object_refs,
        relationship_refs=relationship_refs,
        depths=depths,
        truncated=truncated,
    )


def _ref(
    object_id: str,
    kind: AIResearchObjectKind,
    contract: str,
    version: str | None = None,
    owner: str = "platform-core",
    fingerprint_char: str = "a",
) -> AIResearchObjectEnvelope:
    return AIResearchObjectEnvelope(
        object_ref=AIResearchObjectRef(
            object_id=object_id,
            object_kind=kind,
            contract=contract,
            object_version=version,
            fingerprint_sha256=fingerprint_char * 64,
            product_owner=owner,
            payload_ref=f"core-ref://{object_id}",
        ),
        title=object_id,
        provenance={"unified_registration_only": True},
    )


def reference_unified_ai_research_bundle() -> UnifiedAIResearchObjectBundle:
    bindings = [
        AIResearchContractBinding(
            binding_id="binding:ai-model",
            contract=AI_MODEL_CONTRACT_VERSION,
            introduced_release="3.27.0",
            object_kinds=[AIResearchObjectKind.ai_model, AIResearchObjectKind.ai_model_version],
            source_module="ai_model_objects",
        ),
        AIResearchContractBinding(
            binding_id="binding:ai-training",
            contract=AI_TRAINING_LINEAGE_CONTRACT_VERSION,
            introduced_release="3.28.0",
            object_kinds=[
                AIResearchObjectKind.dataset,
                AIResearchObjectKind.dataset_version,
                AIResearchObjectKind.feature_set,
                AIResearchObjectKind.training_lineage,
            ],
            source_module="ai_training_lineage",
        ),
        AIResearchContractBinding(
            binding_id="binding:ai-inference",
            contract=AI_INFERENCE_CONTRACT_VERSION,
            introduced_release="3.29.0",
            object_kinds=[AIResearchObjectKind.inference_run, AIResearchObjectKind.ai_artifact],
            source_module="ai_inference_provenance",
        ),
        AIResearchContractBinding(
            binding_id="binding:prompt-context-retrieval",
            contract=PROMPT_CONTEXT_CONTRACT_VERSION,
            introduced_release="3.30.0",
            object_kinds=[
                AIResearchObjectKind.prompt,
                AIResearchObjectKind.prompt_version,
                AIResearchObjectKind.retrieval_query,
                AIResearchObjectKind.retrieval_result_set,
                AIResearchObjectKind.context_assembly,
            ],
            source_module="prompt_context_retrieval",
        ),
        AIResearchContractBinding(
            binding_id="binding:ai-evaluation",
            contract=AI_EVALUATION_CONTRACT_VERSION,
            introduced_release="3.31.0",
            object_kinds=[
                AIResearchObjectKind.benchmark,
                AIResearchObjectKind.evaluation_case,
                AIResearchObjectKind.evaluation_run,
                AIResearchObjectKind.benchmark_result,
            ],
            source_module="ai_evaluation_benchmark",
        ),
        AIResearchContractBinding(
            binding_id="binding:ai-experiment",
            contract=AI_EXPERIMENT_CONTRACT_VERSION,
            introduced_release="3.32.0",
            object_kinds=[
                AIResearchObjectKind.experiment,
                AIResearchObjectKind.experiment_run_binding,
                AIResearchObjectKind.reproducibility_package,
                AIResearchObjectKind.reproduction_attempt,
            ],
            source_module="ai_experiment_reproducibility",
        ),
        AIResearchContractBinding(
            binding_id="binding:ai-error-robustness",
            contract=AI_ERROR_ROBUSTNESS_CONTRACT_VERSION,
            introduced_release="3.33.0",
            object_kinds=[
                AIResearchObjectKind.failure_taxonomy,
                AIResearchObjectKind.error_observation,
                AIResearchObjectKind.evaluation_slice,
                AIResearchObjectKind.robustness_test,
                AIResearchObjectKind.robustness_run,
                AIResearchObjectKind.error_analysis_report,
            ],
            source_module="ai_error_robustness",
        ),
        AIResearchContractBinding(
            binding_id="binding:ai-calibration-drift-risk",
            contract=AI_CALIBRATION_DRIFT_RISK_CONTRACT_VERSION,
            introduced_release="3.34.0",
            object_kinds=[
                AIResearchObjectKind.calibration_assessment,
                AIResearchObjectKind.monitoring_window,
                AIResearchObjectKind.drift_signal,
                AIResearchObjectKind.drift_observation,
                AIResearchObjectKind.risk_indicator,
                AIResearchObjectKind.risk_observation,
                AIResearchObjectKind.monitoring_policy,
                AIResearchObjectKind.monitoring_snapshot,
            ],
            source_module="ai_calibration_drift_risk",
        ),
    ]

    manifest = AIResearchSystemManifest(
        manifest_id="ai-research-system-manifest:v1",
        contract_bindings=bindings,
        metadata={
            "object_payloads_duplicated": False,
            "canonical_identity_layer": True,
        },
    )

    objects = [
        _ref(
            "ai-model-version:reference-classifier:1.0.0",
            AIResearchObjectKind.ai_model_version,
            AI_MODEL_CONTRACT_VERSION,
            "1.0.0",
            fingerprint_char="1",
        ),
        _ref(
            "dataset-version:reference-classification:v1",
            AIResearchObjectKind.dataset_version,
            AI_TRAINING_LINEAGE_CONTRACT_VERSION,
            "v1",
            owner="knowledge-library",
            fingerprint_char="2",
        ),
        _ref(
            "training-lineage:reference-classifier:1.0.0",
            AIResearchObjectKind.training_lineage,
            AI_TRAINING_LINEAGE_CONTRACT_VERSION,
            fingerprint_char="3",
        ),
        _ref(
            "prompt-version:research-evidence-synthesis:1.0.0",
            AIResearchObjectKind.prompt_version,
            PROMPT_CONTEXT_CONTRACT_VERSION,
            "1.0.0",
            owner="research-librarian",
            fingerprint_char="4",
        ),
        _ref(
            "context-assembly:reference-evidence-001",
            AIResearchObjectKind.context_assembly,
            PROMPT_CONTEXT_CONTRACT_VERSION,
            owner="research-librarian",
            fingerprint_char="5",
        ),
        _ref(
            "inference-run:reference-classifier:001",
            AIResearchObjectKind.inference_run,
            AI_INFERENCE_CONTRACT_VERSION,
            fingerprint_char="6",
        ),
        _ref(
            "evaluation-run:reference-classifier:001",
            AIResearchObjectKind.evaluation_run,
            AI_EVALUATION_CONTRACT_VERSION,
            fingerprint_char="7",
        ),
        _ref(
            "ai-experiment:reference-classifier-comparison:v1",
            AIResearchObjectKind.experiment,
            AI_EXPERIMENT_CONTRACT_VERSION,
            "v1",
            owner="research-lab",
            fingerprint_char="8",
        ),
        _ref(
            "robustness-run:reference-classifier-noise:001",
            AIResearchObjectKind.robustness_run,
            AI_ERROR_ROBUSTNESS_CONTRACT_VERSION,
            owner="research-lab",
            fingerprint_char="9",
        ),
        _ref(
            "calibration-assessment:reference:current",
            AIResearchObjectKind.calibration_assessment,
            AI_CALIBRATION_DRIFT_RISK_CONTRACT_VERSION,
            owner="research-lab",
            fingerprint_char="a",
        ),
        _ref(
            "drift-observation:reference:current",
            AIResearchObjectKind.drift_observation,
            AI_CALIBRATION_DRIFT_RISK_CONTRACT_VERSION,
            owner="research-lab",
            fingerprint_char="b",
        ),
        _ref(
            "risk-observation:robustness:current",
            AIResearchObjectKind.risk_observation,
            AI_CALIBRATION_DRIFT_RISK_CONTRACT_VERSION,
            owner="research-lab",
            fingerprint_char="c",
        ),
        _ref(
            "monitoring-snapshot:reference:current",
            AIResearchObjectKind.monitoring_snapshot,
            AI_CALIBRATION_DRIFT_RISK_CONTRACT_VERSION,
            owner="research-lab",
            fingerprint_char="d",
        ),
    ]

    registry = AIResearchObjectRegistry(
        registry_id="ai-research-object-registry:reference:v1",
        objects=objects,
        contract_manifest_ref=manifest.manifest_id,
        metadata={"payload_mode": "reference-only"},
    )

    rels = [
        AIResearchRelationship(
            relationship_id="rel:model-trained-on-dataset",
            source_object_ref="ai-model-version:reference-classifier:1.0.0",
            target_object_ref="dataset-version:reference-classification:v1",
            relationship_type=AIResearchRelationshipType.trained_on,
        ),
        AIResearchRelationship(
            relationship_id="rel:model-produced-by-training",
            source_object_ref="ai-model-version:reference-classifier:1.0.0",
            target_object_ref="training-lineage:reference-classifier:1.0.0",
            relationship_type=AIResearchRelationshipType.produced_by,
        ),
        AIResearchRelationship(
            relationship_id="rel:inference-generated-by-model",
            source_object_ref="inference-run:reference-classifier:001",
            target_object_ref="ai-model-version:reference-classifier:1.0.0",
            relationship_type=AIResearchRelationshipType.generated_by,
        ),
        AIResearchRelationship(
            relationship_id="rel:inference-uses-prompt",
            source_object_ref="inference-run:reference-classifier:001",
            target_object_ref="prompt-version:research-evidence-synthesis:1.0.0",
            relationship_type=AIResearchRelationshipType.uses_prompt,
        ),
        AIResearchRelationship(
            relationship_id="rel:inference-uses-context",
            source_object_ref="inference-run:reference-classifier:001",
            target_object_ref="context-assembly:reference-evidence-001",
            relationship_type=AIResearchRelationshipType.uses_context,
        ),
        AIResearchRelationship(
            relationship_id="rel:evaluation-evaluates-model",
            source_object_ref="evaluation-run:reference-classifier:001",
            target_object_ref="ai-model-version:reference-classifier:1.0.0",
            relationship_type=AIResearchRelationshipType.evaluates,
        ),
        AIResearchRelationship(
            relationship_id="rel:evaluation-observes-inference",
            source_object_ref="evaluation-run:reference-classifier:001",
            target_object_ref="inference-run:reference-classifier:001",
            relationship_type=AIResearchRelationshipType.observed_in,
        ),
        AIResearchRelationship(
            relationship_id="rel:experiment-includes-evaluation",
            source_object_ref="ai-experiment:reference-classifier-comparison:v1",
            target_object_ref="evaluation-run:reference-classifier:001",
            relationship_type=AIResearchRelationshipType.includes,
        ),
        AIResearchRelationship(
            relationship_id="rel:robustness-tests-model",
            source_object_ref="robustness-run:reference-classifier-noise:001",
            target_object_ref="ai-model-version:reference-classifier:1.0.0",
            relationship_type=AIResearchRelationshipType.robustness_tested_by,
        ),
        AIResearchRelationship(
            relationship_id="rel:robustness-derived-from-evaluation",
            source_object_ref="robustness-run:reference-classifier-noise:001",
            target_object_ref="evaluation-run:reference-classifier:001",
            relationship_type=AIResearchRelationshipType.derived_from,
        ),
        AIResearchRelationship(
            relationship_id="rel:calibration-evaluates-model",
            source_object_ref="calibration-assessment:reference:current",
            target_object_ref="ai-model-version:reference-classifier:1.0.0",
            relationship_type=AIResearchRelationshipType.calibrated_by,
        ),
        AIResearchRelationship(
            relationship_id="rel:drift-observes-model",
            source_object_ref="drift-observation:reference:current",
            target_object_ref="ai-model-version:reference-classifier:1.0.0",
            relationship_type=AIResearchRelationshipType.drift_observed_by,
        ),
        AIResearchRelationship(
            relationship_id="rel:risk-derived-from-robustness",
            source_object_ref="risk-observation:robustness:current",
            target_object_ref="robustness-run:reference-classifier-noise:001",
            relationship_type=AIResearchRelationshipType.derived_from,
        ),
        AIResearchRelationship(
            relationship_id="rel:snapshot-monitors-model",
            source_object_ref="monitoring-snapshot:reference:current",
            target_object_ref="ai-model-version:reference-classifier:1.0.0",
            relationship_type=AIResearchRelationshipType.monitored_by,
        ),
        AIResearchRelationship(
            relationship_id="rel:snapshot-contains-calibration",
            source_object_ref="monitoring-snapshot:reference:current",
            target_object_ref="calibration-assessment:reference:current",
            relationship_type=AIResearchRelationshipType.contains,
        ),
        AIResearchRelationship(
            relationship_id="rel:snapshot-contains-drift",
            source_object_ref="monitoring-snapshot:reference:current",
            target_object_ref="drift-observation:reference:current",
            relationship_type=AIResearchRelationshipType.contains,
        ),
        AIResearchRelationship(
            relationship_id="rel:snapshot-contains-risk",
            source_object_ref="monitoring-snapshot:reference:current",
            target_object_ref="risk-observation:robustness:current",
            relationship_type=AIResearchRelationshipType.contains,
        ),
    ]

    graph = AIResearchRelationshipGraph(
        graph_id="ai-research-relationship-graph:reference:v1",
        registry_ref=registry.registry_id,
        object_ids=[item.object_ref.object_id for item in objects],
        relationships=rels,
        metadata={"lineage_queryable": True},
    )

    snapshot = AIResearchSnapshot(
        snapshot_id="ai-research-snapshot:reference:v1",
        manifest_ref=manifest.manifest_id,
        registry_ref=registry.registry_id,
        graph_ref=graph.graph_id,
        manifest_fingerprint_sha256=manifest.fingerprint(),
        registry_fingerprint_sha256=registry.fingerprint(),
        graph_fingerprint_sha256=graph.fingerprint(),
        source_release_refs=[
            "v3.27.0",
            "v3.28.0",
            "v3.29.0",
            "v3.30.0",
            "v3.31.0",
            "v3.32.0",
            "v3.33.0",
            "v3.34.0",
        ],
        provenance={
            "unified_without_payload_duplication": True,
            "scientific_validity_certified": False,
        },
    )

    selected_objects = [item.object_ref.object_id for item in objects]
    package = AIResearchPackageManifest(
        package_id="ai-research-package:reference-classifier:v1",
        snapshot_ref=snapshot.snapshot_id,
        selected_object_refs=selected_objects,
        selected_relationship_refs=[item.relationship_id for item in rels],
        root_object_refs=[
            "ai-model-version:reference-classifier:1.0.0",
            "monitoring-snapshot:reference:current",
        ],
        purpose=(
            "Portable research package connecting model lineage, inference, "
            "evaluation, experiment, robustness and monitoring evidence."
        ),
        content_sha256="e" * 64,
    )

    return UnifiedAIResearchObjectBundle(
        manifest=manifest,
        registry=registry,
        graph=graph,
        snapshot=snapshot,
        packages=[package],
    )


def contract_document() -> dict[str, Any]:
    reference = reference_unified_ai_research_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "unifies": [
            AI_MODEL_CONTRACT_VERSION,
            AI_TRAINING_LINEAGE_CONTRACT_VERSION,
            AI_INFERENCE_CONTRACT_VERSION,
            PROMPT_CONTEXT_CONTRACT_VERSION,
            AI_EVALUATION_CONTRACT_VERSION,
            AI_EXPERIMENT_CONTRACT_VERSION,
            AI_ERROR_ROBUSTNESS_CONTRACT_VERSION,
            AI_CALIBRATION_DRIFT_RISK_CONTRACT_VERSION,
        ],
        "runtime_contracts": [
            COMPUTATIONAL_RUNTIME_OBJECT_CONTRACT_VERSION,
            COMPUTATIONAL_JOB_CONTRACT_VERSION,
            ENVIRONMENT_PROVENANCE_CONTRACT_VERSION,
        ],
        "object_types": [
            "AIResearchContractBinding",
            "AIResearchSystemManifest",
            "AIResearchObjectRef",
            "AIResearchObjectEnvelope",
            "AIResearchRelationship",
            "AIResearchObjectRegistry",
            "AIResearchRelationshipGraph",
            "AIResearchLineageQuery",
            "AIResearchLineagePath",
            "AIResearchSnapshot",
            "AIResearchPackageManifest",
            "UnifiedAIResearchObjectBundle",
        ],
        "capabilities": {
            "canonical_cross_contract_identity": True,
            "reference_only_payload_mode": True,
            "cross_product_object_registry": True,
            "typed_relationship_graph": True,
            "upstream_lineage_queries": True,
            "downstream_lineage_queries": True,
            "relationship_filtered_lineage": True,
            "versioned_system_manifest": True,
            "immutable_snapshot_fingerprints": True,
            "portable_ai_research_packages": True,
            "model_to_monitoring_traceability": True,
            "monitoring_to_training_traceability": True,
        },
        "integration": {
            "core_unifies_without_replacing_source_contracts": True,
            "core_duplicates_source_payloads": False,
            "knowledge_library_objects_remain_owned_by_library": True,
            "research_librarian_objects_remain_owned_by_librarian": True,
            "research_lab_objects_remain_owned_by_lab": True,
            "workspace_runtime_objects_remain_execution_owned": True,
        },
        "reference": {
            "manifest_id": reference.manifest.manifest_id,
            "registry_id": reference.registry.registry_id,
            "graph_id": reference.graph.graph_id,
            "snapshot_id": reference.snapshot.snapshot_id,
            "bundle_fingerprint_sha256": reference.fingerprint(),
            "registered_object_count": len(reference.registry.objects),
            "relationship_count": len(reference.graph.relationships),
        },
        "boundaries": {
            "core_executes_ai_jobs": False,
            "core_materializes_source_payloads": False,
            "core_selects_best_model": False,
            "core_certifies_scientific_validity": False,
            "core_autonomously_changes_research_objects": False,
            "core_owns_identity_lineage_graph_and_exchange_contracts": True,
        },
    }
