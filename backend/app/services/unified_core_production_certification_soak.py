from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .entity_evidence_runtime_performance_scale import CONTRACT_VERSION as V398_CONTRACT
from .unified_runtime_observability_audit_drift_intelligence import CONTRACT_VERSION as V397_CONTRACT
from .federation_governance_trust_policy_runtime import CONTRACT_VERSION as V396_CONTRACT
from .signed_runtime_artifacts_execution_attestations import CONTRACT_VERSION as V395_CONTRACT

CORE_RELEASE = "3.99.0"
CONTRACT_VERSION = "sc.core.unified-core-production-certification-soak.v1"


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


class GateStatus(str, Enum):
    pass_ = "pass"
    warn = "warn"
    fail = "fail"
    pending = "pending"


class ReadinessDisposition(str, Enum):
    approved_for_controlled_soak = "approved-for-controlled-soak"
    production_certified = "production-certified"
    blocked = "blocked"


class ProductionCertificationPolicy(BaseModel):
    policy_id: str = Field(min_length=3, max_length=500)
    required_contract_start_release: Literal["3.57.0"] = "3.57.0"
    required_contract_end_release: Literal["3.98.0"] = "3.98.0"
    require_all_contracts_identified: Literal[True] = True
    require_route_and_schema_certification: Literal[True] = True
    require_zero_critical_failures: Literal[True] = True
    require_reproducible_validation: Literal[True] = True
    require_recovery_readiness: Literal[True] = True
    require_observability_and_slo_gates: Literal[True] = True
    require_federation_and_signature_policy_checks: Literal[True] = True
    minimum_controlled_soak_hours: int = Field(default=24, ge=1)
    recommended_extended_soak_hours: int = Field(default=72, ge=24)
    certification_is_not_scientific_truth: Literal[True] = True
    certification_is_not_evidence_validation: Literal[True] = True
    certification_may_not_mutate_governed_graphs: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    def fingerprint(self) -> str: return canonical_sha256(self)


class ContractCertificationRecord(BaseModel):
    release: str = Field(pattern=r"^3\.\d+\.\d+$")
    module: str = Field(min_length=2, max_length=500)
    contract: str = Field(min_length=8, max_length=1000)
    status: GateStatus
    route_mounted: bool
    schema_available: bool
    compatibility_state: Literal["certified", "qualified", "blocked"]
    certification_does_not_promote_epistemic_state: Literal[True] = True
    def fingerprint(self) -> str: return canonical_sha256(self)


class CertificationGate(BaseModel):
    gate_id: str = Field(min_length=3, max_length=500)
    category: Literal["contracts", "routes", "schemas", "tests", "reproducibility", "performance", "observability", "security-governance", "federation", "recovery", "wordpress", "release-integrity"]
    status: GateStatus
    evidence_refs: list[str] = Field(min_length=1)
    blocking: bool
    qualification: str | None = None
    measured_state_is_operational_evidence_only: Literal[True] = True
    @model_validator(mode="after")
    def validate_refs(self):
        _unique(self.evidence_refs, "evidence_refs")
        if self.status == GateStatus.fail and not self.blocking:
            raise ValueError("failed certification gate must be blocking")
        return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class RouteSurfaceCertification(BaseModel):
    surface_id: str = Field(min_length=3, max_length=500)
    surface_kind: Literal["private-api", "public-api", "health", "wordpress-connector"]
    status: GateStatus
    expected_behavior: str = Field(min_length=3, max_length=2000)
    version_identity_required: Literal[True] = True
    contract_identity_required: bool = True
    def fingerprint(self) -> str: return canonical_sha256(self)


class RecoveryReadinessRecord(BaseModel):
    recovery_id: str = Field(min_length=3, max_length=500)
    capability: Literal["backup", "rollback", "restore", "tagged-source-promotion"]
    status: GateStatus
    evidence_ref: str = Field(min_length=3, max_length=1000)
    destructive_cleanup_required: Literal[False] = False
    preserves_unrelated_local_state: Literal[True] = True
    def fingerprint(self) -> str: return canonical_sha256(self)


class SoakPolicy(BaseModel):
    soak_policy_id: str = Field(min_length=3, max_length=500)
    minimum_hours: int = Field(ge=1)
    recommended_hours: int = Field(ge=1)
    required_health_checks: list[str] = Field(min_length=1)
    allowed_critical_failures: Literal[0] = 0
    allowed_data_integrity_failures: Literal[0] = 0
    require_no_unexplained_graph_mutation: Literal[True] = True
    require_alert_and_drift_capture: Literal[True] = True
    @model_validator(mode="after")
    def validate_hours(self):
        if self.recommended_hours < self.minimum_hours:
            raise ValueError("recommended soak must be >= minimum soak")
        _unique(self.required_health_checks, "required_health_checks")
        return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class SoakObservation(BaseModel):
    observation_id: str = Field(min_length=3, max_length=500)
    phase: Literal["preflight", "controlled-soak", "extended-soak"]
    observed_hours: float = Field(ge=0)
    status: GateStatus
    health_passes: int = Field(ge=0)
    health_failures: int = Field(ge=0)
    critical_failures: int = Field(ge=0)
    data_integrity_failures: int = Field(ge=0)
    qualification: str
    observation_is_not_claim_truth_verdict: Literal[True] = True
    def fingerprint(self) -> str: return canonical_sha256(self)


class CertificationQualification(BaseModel):
    qualification_id: str = Field(min_length=3, max_length=500)
    source_ref: str = Field(min_length=3, max_length=1000)
    severity: Literal["info", "warning"]
    description: str = Field(min_length=10, max_length=3000)
    blocks_controlled_soak: bool
    requires_follow_up: bool
    def fingerprint(self) -> str: return canonical_sha256(self)


class ProductionReadinessDecision(BaseModel):
    decision_id: str = Field(min_length=3, max_length=500)
    disposition: ReadinessDisposition
    blocking_gate_refs: list[str] = Field(default_factory=list)
    qualification_refs: list[str] = Field(default_factory=list)
    controlled_soak_required: Literal[True] = True
    minimum_soak_hours: int = Field(ge=1)
    full_production_certification_requires_elapsed_soak: Literal[True] = True
    decision_is_operational_not_epistemic: Literal[True] = True
    no_graph_mutation_authorized: Literal[True] = True
    @model_validator(mode="after")
    def validate_refs(self):
        _unique(self.blocking_gate_refs, "blocking_gate_refs")
        _unique(self.qualification_refs, "qualification_refs")
        if self.disposition == ReadinessDisposition.production_certified:
            raise ValueError("reference package cannot claim elapsed production soak")
        return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class ProductionCertificationTrace(BaseModel):
    trace_id: str = Field(min_length=3, max_length=500)
    contract_record_refs: list[str] = Field(min_length=1)
    gate_refs: list[str] = Field(min_length=1)
    route_surface_refs: list[str] = Field(min_length=1)
    recovery_refs: list[str] = Field(min_length=1)
    soak_observation_refs: list[str] = Field(min_length=1)
    qualification_refs: list[str] = Field(default_factory=list)
    decision_ref: str = Field(min_length=3, max_length=500)
    started_at: str = Field(min_length=10, max_length=80)
    completed_at: str = Field(min_length=10, max_length=80)
    reproducible: Literal[True] = True
    trace_preserves_qualifications: Literal[True] = True
    def fingerprint(self) -> str: return canonical_sha256(self)


class ProductionCertificationSnapshot(BaseModel):
    snapshot_id: str = Field(min_length=3, max_length=500)
    policy_ref: str = Field(min_length=3, max_length=500)
    contract_record_refs: list[str] = Field(min_length=1)
    gate_refs: list[str] = Field(min_length=1)
    route_surface_refs: list[str] = Field(min_length=1)
    recovery_refs: list[str] = Field(min_length=1)
    soak_policy_ref: str = Field(min_length=3, max_length=500)
    soak_observation_refs: list[str] = Field(min_length=1)
    qualification_refs: list[str] = Field(default_factory=list)
    decision_ref: str = Field(min_length=3, max_length=500)
    trace_ref: str = Field(min_length=3, max_length=500)
    as_of: str = Field(min_length=10, max_length=80)
    immutable: Literal[True] = True
    supersedable: Literal[True] = True
    snapshot_is_not_scientific_or_evidentiary_truth: Literal[True] = True
    def fingerprint(self) -> str: return canonical_sha256(self)


class UnifiedCoreProductionCertificationSoakBundle(BaseModel):
    release: Literal["3.99.0"] = "3.99.0"
    contract: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    policy: ProductionCertificationPolicy
    contract_records: list[ContractCertificationRecord] = Field(min_length=1)
    gates: list[CertificationGate] = Field(min_length=1)
    route_surfaces: list[RouteSurfaceCertification] = Field(min_length=1)
    recovery_records: list[RecoveryReadinessRecord] = Field(min_length=1)
    soak_policy: SoakPolicy
    soak_observations: list[SoakObservation] = Field(min_length=1)
    qualifications: list[CertificationQualification] = Field(default_factory=list)
    decision: ProductionReadinessDecision
    traces: list[ProductionCertificationTrace] = Field(min_length=1)
    snapshots: list[ProductionCertificationSnapshot] = Field(min_length=1)
    database_migration: Literal["none"] = "none"

    @model_validator(mode="after")
    def validate_bundle(self):
        _unique([x.contract for x in self.contract_records], "contracts")
        _unique([x.gate_id for x in self.gates], "gate_ids")
        _unique([x.surface_id for x in self.route_surfaces], "surface_ids")
        _unique([x.recovery_id for x in self.recovery_records], "recovery_ids")
        _unique([x.observation_id for x in self.soak_observations], "soak_observation_ids")
        _unique([x.qualification_id for x in self.qualifications], "qualification_ids")
        _unique([x.trace_id for x in self.traces], "trace_ids")
        _unique([x.snapshot_id for x in self.snapshots], "snapshot_ids")
        if len(self.contract_records) != 42:
            raise ValueError("v3.99 reference certification requires the 42 contracts from v3.57-v3.98")
        if any(x.status == GateStatus.fail for x in self.gates):
            raise ValueError("reference certification contains blocking failure")
        return self

    def fingerprint(self) -> str: return canonical_sha256(self)


@lru_cache(maxsize=1)
def reference_unified_core_production_certification_soak_bundle() -> UnifiedCoreProductionCertificationSoakBundle:
    policy = ProductionCertificationPolicy(policy_id="unified-core-production-certification-policy-v1")
    contracts = [
        ContractCertificationRecord(release="3.57.0", module="machine_learning_models", contract="sc.core.machine-learning-neural-model-object.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
        ContractCertificationRecord(release="3.58.0", module="ml_training_lineage", contract="sc.core.training-run-checkpoint-experiment-lineage.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
        ContractCertificationRecord(release="3.59.0", module="ml_dataset_provenance", contract="sc.core.neural-dataset-feature-transformation-provenance.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
        ContractCertificationRecord(release="3.60.0", module="ml_evaluation_uncertainty", contract="sc.core.neural-evaluation-calibration-uncertainty.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
        ContractCertificationRecord(release="3.61.0", module="ml_explainability_interpretation", contract="sc.core.explainability-model-interpretation.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
        ContractCertificationRecord(release="3.62.0", module="ml_embedding_representation", contract="sc.core.neural-embedding-representation-intelligence.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
        ContractCertificationRecord(release="3.63.0", module="ml_inference_prediction_provenance", contract="sc.core.neural-inference-prediction-provenance.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
        ContractCertificationRecord(release="3.64.0", module="ml_model_registry_packages", contract="sc.core.neural-model-registry-reproducible-packages.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
        ContractCertificationRecord(release="3.65.0", module="multilingual_text_language", contract="sc.core.multilingual-text-language-object.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
        ContractCertificationRecord(release="3.66.0", module="linguistic_annotation", contract="sc.core.linguistic-annotation-provenance.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
        ContractCertificationRecord(release="3.67.0", module="translation_alignment", contract="sc.core.translation-transliteration-alignment.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
        ContractCertificationRecord(release="3.68.0", module="historical_language_variant", contract="sc.core.historical-language-script-orthography-variant.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
        ContractCertificationRecord(release="3.69.0", module="cross_lingual_semantic_exchange", contract="sc.core.cross-lingual-semantic-linguistic-exchange.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
        ContractCertificationRecord(release="3.70.0", module="graph_machine_learning", contract="sc.core.graph-machine-learning-foundation.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
        ContractCertificationRecord(release="3.71.0", module="graph_embedding_runtime", contract="sc.core.graph-embedding-runtime.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
        ContractCertificationRecord(release="3.72.0", module="graph_classification", contract="sc.core.graph-node-edge-classification.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
        ContractCertificationRecord(release="3.73.0", module="graph_link_prediction", contract="sc.core.graph-link-prediction-candidate-relationship.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
        ContractCertificationRecord(release="3.74.0", module="graph_anomaly_detection", contract="sc.core.graph-anomaly-detection.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
        ContractCertificationRecord(release="3.75.0", module="knowledge_graph_representation_learning", contract="sc.core.knowledge-graph-representation-learning.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
        ContractCertificationRecord(release="3.76.0", module="evidence_graph_neural_validation", contract="sc.core.evidence-graph-neural-analysis-validation.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
        ContractCertificationRecord(release="3.77.0", module="entity_resolution_identity_graph", contract="sc.core.entity-resolution-identity-graph-foundation.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
        ContractCertificationRecord(release="3.78.0", module="temporal_identity_intelligence", contract="sc.core.temporal-identity-alias-name-variant-intelligence.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
        ContractCertificationRecord(release="3.79.0", module="probabilistic_record_linkage", contract="sc.core.probabilistic-record-linkage-entity-matching.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
        ContractCertificationRecord(release="3.80.0", module="cross_source_entity_reconciliation", contract="sc.core.cross-source-entity-reconciliation-identity-provenance.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
        ContractCertificationRecord(release="3.81.0", module="public_record_documentary_source", contract="sc.core.public-record-documentary-source-object-model.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
        ContractCertificationRecord(release="3.82.0", module="relationship_discovery_hypotheses", contract="sc.core.relationship-discovery-connection-hypothesis.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
        ContractCertificationRecord(release="3.83.0", module="network_structure_community_motif", contract="sc.core.network-structure-community-motif-intelligence.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
        ContractCertificationRecord(release="3.84.0", module="explainable_connection_paths_evidence_chains", contract="sc.core.explainable-connection-paths-evidence-chains.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
        ContractCertificationRecord(release="3.85.0", module="multi_hop_research_investigation_graph_reasoning", contract="sc.core.multi-hop-research-investigation-graph-reasoning.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
        ContractCertificationRecord(release="3.86.0", module="contradictory_identity_relationship_resolution", contract="sc.core.contradictory-identity-relationship-resolution.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
        ContractCertificationRecord(release="3.87.0", module="entity_centric_timeline_event_association", contract="sc.core.entity-centric-timeline-event-association.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
        ContractCertificationRecord(release="3.88.0", module="reproducible_graph_investigation_package", contract="sc.core.reproducible-graph-investigation-package.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
        ContractCertificationRecord(release="3.89.0", module="federated_evidence_graph_exchange", contract="sc.core.federated-evidence-graph-exchange.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
        ContractCertificationRecord(release="3.90.0", module="unified_entity_evidence_intelligence_runtime", contract="sc.core.unified-entity-evidence-intelligence-runtime.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
        ContractCertificationRecord(release="3.91.0", module="unified_runtime_policy_capability_negotiation", contract="sc.core.unified-runtime-policy-capability-negotiation.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
        ContractCertificationRecord(release="3.92.0", module="unified_entity_evidence_query_api", contract="sc.core.unified-entity-evidence-query-api.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
        ContractCertificationRecord(release="3.93.0", module="investigation_session_research_context_runtime", contract="sc.core.investigation-session-research-context-runtime.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
        ContractCertificationRecord(release="3.94.0", module="cross_product_intelligence_handoff", contract="sc.core.cross-product-intelligence-handoff.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
        ContractCertificationRecord(release="3.95.0", module="signed_runtime_artifacts_execution_attestations", contract="sc.core.signed-runtime-artifacts-execution-attestations.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
        ContractCertificationRecord(release="3.96.0", module="federation_governance_trust_policy_runtime", contract="sc.core.federation-governance-trust-policy-runtime.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
        ContractCertificationRecord(release="3.97.0", module="unified_runtime_observability_audit_drift_intelligence", contract="sc.core.unified-runtime-observability-audit-drift-intelligence.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
        ContractCertificationRecord(release="3.98.0", module="entity_evidence_runtime_performance_scale", contract="sc.core.entity-evidence-runtime-performance-scale.v1", status="pass", route_mounted=True, schema_available=True, compatibility_state="certified"),
    ]
    gates = [
        CertificationGate(gate_id="gate-contract-inventory", category="contracts", status="pass", evidence_refs=["42-contracts-v357-v398"], blocking=True),
        CertificationGate(gate_id="gate-route-mounts", category="routes", status="pass", evidence_refs=["fastapi-route-inventory"], blocking=True),
        CertificationGate(gate_id="gate-json-schemas", category="schemas", status="pass", evidence_refs=["schema-generation"], blocking=True),
        CertificationGate(gate_id="gate-targeted-tests", category="tests", status="pass", evidence_refs=["pytest-v399-targeted"], blocking=True),
        CertificationGate(gate_id="gate-reproducibility", category="reproducibility", status="pass", evidence_refs=["bundle-fingerprint-roundtrip"], blocking=True),
        CertificationGate(gate_id="gate-performance", category="performance", status="warn", evidence_refs=[V398_CONTRACT], blocking=False, qualification="v3.98 contains one intentional benchmark warning at the 1m-node traversal envelope."),
        CertificationGate(gate_id="gate-observability", category="observability", status="pass", evidence_refs=[V397_CONTRACT], blocking=True),
        CertificationGate(gate_id="gate-signing-governance", category="security-governance", status="pass", evidence_refs=[V395_CONTRACT, V396_CONTRACT], blocking=True),
        CertificationGate(gate_id="gate-federation", category="federation", status="pass", evidence_refs=[V396_CONTRACT], blocking=True),
        CertificationGate(gate_id="gate-recovery", category="recovery", status="pass", evidence_refs=["backup-before-promote", "remote-tag-match", "ff-only-production-pull"], blocking=True),
        CertificationGate(gate_id="gate-wordpress", category="wordpress", status="pass", evidence_refs=["canonical-plugin-slug:sustainable-catalyst-platform-core"], blocking=True),
        CertificationGate(gate_id="gate-release-integrity", category="release-integrity", status="pass", evidence_refs=["sha256-release-bundle", "zip-integrity"], blocking=True),
    ]
    routes = [
        RouteSurfaceCertification(surface_id="surface-health", surface_kind="health", status="pass", expected_behavior="Health endpoint reports Core release identity and operational status.", contract_identity_required=False),
        RouteSurfaceCertification(surface_id="surface-private-api", surface_kind="private-api", status="pass", expected_behavior="Private certification API exposes reference, validation, and contract operations."),
        RouteSurfaceCertification(surface_id="surface-public-api", surface_kind="public-api", status="pass", expected_behavior="Public certification contract exposes bounded production-readiness semantics."),
        RouteSurfaceCertification(surface_id="surface-wordpress", surface_kind="wordpress-connector", status="pass", expected_behavior="Canonical WordPress slug upgrades the existing connector in place.", contract_identity_required=False),
    ]
    recovery = [
        RecoveryReadinessRecord(recovery_id="recovery-backup", capability="backup", status="pass", evidence_ref="backup-before-promote"),
        RecoveryReadinessRecord(recovery_id="recovery-rollback", capability="rollback", status="pass", evidence_ref="tagged-previous-head"),
        RecoveryReadinessRecord(recovery_id="recovery-restore", capability="restore", status="pass", evidence_ref="repository-and-backend-packages"),
        RecoveryReadinessRecord(recovery_id="recovery-tagged-promotion", capability="tagged-source-promotion", status="pass", evidence_ref="remote-tag-head-alignment"),
    ]
    soak_policy = SoakPolicy(
        soak_policy_id="unified-core-controlled-soak-v1",
        minimum_hours=24,
        recommended_hours=72,
        required_health_checks=["health", "contract-identity", "error-rate", "latency", "memory", "container-restarts", "drift-alerts", "data-integrity"],
    )
    soak_observations = [
        SoakObservation(observation_id="soak-preflight", phase="preflight", observed_hours=0, status="pass", health_passes=8, health_failures=0, critical_failures=0, data_integrity_failures=0, qualification="Preflight certification is complete; elapsed controlled production soak begins only after deployment."),
        SoakObservation(observation_id="soak-controlled-window", phase="controlled-soak", observed_hours=0, status="pending", health_passes=0, health_failures=0, critical_failures=0, data_integrity_failures=0, qualification="Minimum 24-hour controlled soak remains an elapsed-time production gate and is intentionally not fabricated by the release package."),
        SoakObservation(observation_id="soak-extended-window", phase="extended-soak", observed_hours=0, status="pending", health_passes=0, health_failures=0, critical_failures=0, data_integrity_failures=0, qualification="Recommended 72-hour extended soak remains pending after deployment."),
    ]
    qualifications = [
        CertificationQualification(qualification_id="qualification-v398-benchmark-warning", source_ref=V398_CONTRACT, severity="warning", description="The v3.98 reference scale profile intentionally records one warning at the 1m-node graph traversal envelope; bounded/degraded semantics remain explicit and non-authority-increasing.", blocks_controlled_soak=False, requires_follow_up=True),
        CertificationQualification(qualification_id="qualification-soak-elapsed-time", source_ref="soak-controlled-window", severity="info", description="Full production certification is intentionally withheld until the minimum controlled soak window has actually elapsed without blocking failures.", blocks_controlled_soak=False, requires_follow_up=True),
    ]
    decision = ProductionReadinessDecision(
        decision_id="decision-v399-preflight",
        disposition="approved-for-controlled-soak",
        blocking_gate_refs=[],
        qualification_refs=[x.qualification_id for x in qualifications],
        minimum_soak_hours=24,
    )
    trace = ProductionCertificationTrace(
        trace_id="production-certification-trace-v399",
        contract_record_refs=[x.contract for x in contracts],
        gate_refs=[x.gate_id for x in gates],
        route_surface_refs=[x.surface_id for x in routes],
        recovery_refs=[x.recovery_id for x in recovery],
        soak_observation_refs=[x.observation_id for x in soak_observations],
        qualification_refs=[x.qualification_id for x in qualifications],
        decision_ref=decision.decision_id,
        started_at="2026-10-01T06:45:00Z",
        completed_at="2026-10-01T07:00:00Z",
    )
    snapshot = ProductionCertificationSnapshot(
        snapshot_id="production-certification-snapshot-v399",
        policy_ref=policy.policy_id,
        contract_record_refs=[x.contract for x in contracts],
        gate_refs=[x.gate_id for x in gates],
        route_surface_refs=[x.surface_id for x in routes],
        recovery_refs=[x.recovery_id for x in recovery],
        soak_policy_ref=soak_policy.soak_policy_id,
        soak_observation_refs=[x.observation_id for x in soak_observations],
        qualification_refs=[x.qualification_id for x in qualifications],
        decision_ref=decision.decision_id,
        trace_ref=trace.trace_id,
        as_of="2026-10-01T07:00:00Z",
    )
    return UnifiedCoreProductionCertificationSoakBundle(
        policy=policy,
        contract_records=contracts,
        gates=gates,
        route_surfaces=routes,
        recovery_records=recovery,
        soak_policy=soak_policy,
        soak_observations=soak_observations,
        qualifications=qualifications,
        decision=decision,
        traces=[trace],
        snapshots=[snapshot],
    )


def contract_document() -> dict[str, Any]:
    b = reference_unified_core_production_certification_soak_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "certification_scope": {"from_release": "3.57.0", "through_release": "3.98.0", "contracts": len(b.contract_records)},
        "principles": {
            "all_governed_contracts_are_independently_identified": True,
            "route_and_schema_certification_are_required": True,
            "reproducible_validation_is_required": True,
            "performance_qualifications_are_preserved": True,
            "observability_and_slo_gates_are_required": True,
            "federation_and_signature_governance_are_required": True,
            "rollback_and_recovery_readiness_are_required": True,
            "full_production_certification_requires_elapsed_soak": True,
            "certification_snapshot_is_supersedable": True,
        },
        "boundaries": {
            "operational_certification_establishes_scientific_truth": False,
            "operational_certification_establishes_evidence_validity": False,
            "benchmark_pass_establishes_claim_truth": False,
            "soak_pass_establishes_claim_truth": False,
            "health_check_failure_establishes_claim_falsity": False,
            "certification_may_silently_drop_qualifications": False,
            "certification_may_bypass_local_validation": False,
            "production_certification_claimed_before_elapsed_soak": False,
            "identity_graph_mutation_performed": False,
            "relationship_graph_mutation_performed": False,
            "evidence_graph_mutation_performed": False,
        },
        "reference": {
            "contracts": len(b.contract_records),
            "gates": len(b.gates),
            "gate_passes": sum(x.status == GateStatus.pass_ for x in b.gates),
            "gate_warnings": sum(x.status == GateStatus.warn for x in b.gates),
            "route_surfaces": len(b.route_surfaces),
            "recovery_records": len(b.recovery_records),
            "soak_observations": len(b.soak_observations),
            "soak_pending": sum(x.status == GateStatus.pending for x in b.soak_observations),
            "qualifications": len(b.qualifications),
            "decision": b.decision.disposition.value,
            "minimum_soak_hours": b.decision.minimum_soak_hours,
            "snapshots": len(b.snapshots),
            "bundle_fingerprint_sha256": b.fingerprint(),
        },
        "database_migration": "none",
    }
