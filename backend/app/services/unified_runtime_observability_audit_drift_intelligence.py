from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .unified_entity_evidence_intelligence_runtime import CONTRACT_VERSION as V390_CONTRACT
from .unified_runtime_policy_capability_negotiation import CONTRACT_VERSION as V391_CONTRACT
from .unified_entity_evidence_query_api import CONTRACT_VERSION as V392_CONTRACT
from .investigation_session_research_context_runtime import CONTRACT_VERSION as V393_CONTRACT
from .cross_product_intelligence_handoff import CONTRACT_VERSION as V394_CONTRACT
from .signed_runtime_artifacts_execution_attestations import CONTRACT_VERSION as V395_CONTRACT
from .federation_governance_trust_policy_runtime import (
    CONTRACT_VERSION as V396_CONTRACT,
    reference_federation_governance_trust_policy_bundle,
)

CORE_RELEASE = "3.97.0"
CONTRACT_VERSION = "sc.core.unified-runtime-observability-audit-drift-intelligence.v1"


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


class ObservationKind(str, Enum):
    runtime_health = "runtime-health"
    contract_health = "contract-health"
    provenance_integrity = "provenance-integrity"
    drift = "drift"
    stale_evidence = "stale-evidence"
    federation_policy = "federation-policy"
    slo = "slo"
    audit = "audit"


class HealthState(str, Enum):
    healthy = "healthy"
    degraded = "degraded"
    unavailable = "unavailable"
    unknown = "unknown"


class DriftKind(str, Enum):
    runtime = "runtime"
    model = "model"
    contract = "contract"
    provenance = "provenance"
    federation_policy = "federation-policy"
    evidence_freshness = "evidence-freshness"


class DriftSeverity(str, Enum):
    informational = "informational"
    low = "low"
    moderate = "moderate"
    high = "high"
    critical = "critical"


class AlertDisposition(str, Enum):
    observe = "observe"
    investigate = "investigate"
    remediate = "remediate"
    quarantine_runtime_output = "quarantine-runtime-output"
    resolved = "resolved"


class ObservabilityPolicy(BaseModel):
    policy_id: str = Field(min_length=3, max_length=500)
    require_runtime_health_observations: Literal[True] = True
    require_contract_health_observations: Literal[True] = True
    require_provenance_gap_detection: Literal[True] = True
    require_explicit_drift_baselines: Literal[True] = True
    require_stale_evidence_signals: Literal[True] = True
    require_federation_policy_drift_detection: Literal[True] = True
    require_slo_indicators: Literal[True] = True
    require_immutable_audit_events: Literal[True] = True
    require_alert_decision_provenance: Literal[True] = True
    require_human_or_policy_review_for_epistemic_change: Literal[True] = True
    anomaly_establishes_claim_false: Literal[False] = False
    drift_establishes_claim_false: Literal[False] = False
    failed_health_check_invalidates_evidence: Literal[False] = False
    alert_promotes_or_demotes_epistemic_state: Literal[False] = False
    observability_mutates_governed_graphs: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    def fingerprint(self) -> str: return canonical_sha256(self)


class RuntimeHealthObservation(BaseModel):
    observation_id: str = Field(min_length=3, max_length=500)
    capability: str = Field(min_length=3, max_length=500)
    contract: str = Field(min_length=3, max_length=500)
    endpoint: str = Field(min_length=1, max_length=1000)
    state: HealthState
    latency_ms: float = Field(ge=0)
    observed_at: str = Field(min_length=10, max_length=80)
    source: str = Field(min_length=2, max_length=500)
    audit_refs: list[str] = Field(default_factory=list)
    operational_observation_not_claim_truth: Literal[True] = True
    health_state_does_not_change_epistemic_state: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_refs(self): _unique(self.audit_refs,"audit_refs"); return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class ContractHealthObservation(BaseModel):
    contract_health_id: str = Field(min_length=3, max_length=500)
    contract: str = Field(min_length=3, max_length=500)
    expected_version: str = Field(min_length=1, max_length=100)
    observed_version: str = Field(min_length=1, max_length=100)
    schema_fingerprint_expected: str = Field(min_length=64, max_length=64)
    schema_fingerprint_observed: str = Field(min_length=64, max_length=64)
    compatible: bool
    observed_at: str = Field(min_length=10, max_length=80)
    mismatch_is_operational_signal_not_content_truth: Literal[True] = True
    mismatch_does_not_invalidate_historical_objects: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    def fingerprint(self) -> str: return canonical_sha256(self)


class RuntimeAuditEvent(BaseModel):
    audit_event_id: str = Field(min_length=3, max_length=500)
    event_type: str = Field(min_length=2, max_length=500)
    actor_or_runtime: str = Field(min_length=2, max_length=500)
    target_ref: str = Field(min_length=2, max_length=1000)
    related_refs: list[str] = Field(default_factory=list)
    recorded_at: str = Field(min_length=10, max_length=80)
    deterministic_event_sha256: str = Field(min_length=64, max_length=64)
    immutable: Literal[True] = True
    event_is_audit_record_not_truth_assessment: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_refs(self): _unique(self.related_refs,"related_refs"); return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class ProvenanceGapSignal(BaseModel):
    provenance_gap_id: str = Field(min_length=3, max_length=500)
    target_object_ref: str = Field(min_length=3, max_length=1000)
    expected_provenance_kind: str = Field(min_length=2, max_length=500)
    missing_or_incomplete_refs: list[str] = Field(min_length=1)
    detected_at: str = Field(min_length=10, max_length=80)
    severity: DriftSeverity
    gap_requires_review: Literal[True] = True
    gap_is_not_proof_object_is_false: Literal[True] = True
    gap_does_not_delete_or_rewrite_object: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_refs(self): _unique(self.missing_or_incomplete_refs,"missing_or_incomplete_refs"); return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class DriftBaseline(BaseModel):
    baseline_id: str = Field(min_length=3, max_length=500)
    drift_kind: DriftKind
    target_ref: str = Field(min_length=3, max_length=1000)
    metric_name: str = Field(min_length=2, max_length=500)
    baseline_value: float
    tolerance_absolute: float = Field(ge=0)
    established_at: str = Field(min_length=10, max_length=80)
    provenance_refs: list[str] = Field(min_length=1)
    baseline_is_comparison_reference_not_truth: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_refs(self): _unique(self.provenance_refs,"provenance_refs"); return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class DriftObservation(BaseModel):
    drift_id: str = Field(min_length=3, max_length=500)
    baseline_ref: str = Field(min_length=3, max_length=500)
    drift_kind: DriftKind
    target_ref: str = Field(min_length=3, max_length=1000)
    observed_value: float
    delta_absolute: float = Field(ge=0)
    outside_tolerance: bool
    severity: DriftSeverity
    observed_at: str = Field(min_length=10, max_length=80)
    evidence_refs: list[str] = Field(min_length=1)
    drift_is_diagnostic_not_truth_verdict: Literal[True] = True
    drift_does_not_change_epistemic_state: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_refs(self): _unique(self.evidence_refs,"evidence_refs"); return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class StaleEvidenceSignal(BaseModel):
    stale_signal_id: str = Field(min_length=3, max_length=500)
    evidence_ref: str = Field(min_length=3, max_length=1000)
    last_validated_at: str = Field(min_length=10, max_length=80)
    freshness_policy_days: int = Field(ge=1)
    age_days: int = Field(ge=0)
    stale: bool
    detected_at: str = Field(min_length=10, max_length=80)
    stale_does_not_mean_false: Literal[True] = True
    stale_requires_revalidation_not_deletion: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    def fingerprint(self) -> str: return canonical_sha256(self)


class FederationPolicyDriftSignal(BaseModel):
    federation_policy_drift_id: str = Field(min_length=3, max_length=500)
    node_ref: str = Field(min_length=3, max_length=500)
    policy_ref: str = Field(min_length=3, max_length=500)
    previous_decision_ref: str = Field(min_length=3, max_length=500)
    current_state: str = Field(min_length=2, max_length=500)
    drift_kind: Literal["permission-change","trust-scope-change","node-state-change","verification-state-change"]
    detected_at: str = Field(min_length=10, max_length=80)
    prior_remote_objects_remain_historical_records: Literal[True] = True
    policy_drift_does_not_establish_content_truth_or_falsity: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    def fingerprint(self) -> str: return canonical_sha256(self)


class RuntimeSLOIndicator(BaseModel):
    slo_indicator_id: str = Field(min_length=3, max_length=500)
    service_or_capability: str = Field(min_length=2, max_length=500)
    metric_name: str = Field(min_length=2, max_length=500)
    objective: float
    observed: float
    compliant: bool
    window: str = Field(min_length=2, max_length=200)
    observed_at: str = Field(min_length=10, max_length=80)
    slo_breach_is_operational_not_epistemic: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    def fingerprint(self) -> str: return canonical_sha256(self)


class ObservabilityAlertDecision(BaseModel):
    alert_id: str = Field(min_length=3, max_length=500)
    signal_refs: list[str] = Field(min_length=1)
    severity: DriftSeverity
    disposition: AlertDisposition
    rationale: str = Field(min_length=3, max_length=3000)
    decided_at: str = Field(min_length=10, max_length=80)
    requires_review: bool
    alert_is_not_truth_verdict: Literal[True] = True
    alert_cannot_promote_or_demote_epistemic_state: Literal[True] = True
    automatic_evidence_deletion_allowed: Literal[False] = False
    automatic_graph_mutation_allowed: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_refs(self): _unique(self.signal_refs,"signal_refs"); return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class ObservabilityTrace(BaseModel):
    trace_id: str = Field(min_length=3, max_length=500)
    observation_refs: list[str] = Field(min_length=1)
    audit_event_refs: list[str] = Field(min_length=1)
    alert_refs: list[str] = Field(min_length=1)
    started_at: str = Field(min_length=10, max_length=80)
    completed_at: str = Field(min_length=10, max_length=80)
    reproducible: Literal[True] = True
    trace_is_diagnostic_not_research_conclusion: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_refs(self):
        for vals,label in ((self.observation_refs,"observation_refs"),(self.audit_event_refs,"audit_event_refs"),(self.alert_refs,"alert_refs")): _unique(vals,label)
        return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class ObservabilitySnapshot(BaseModel):
    snapshot_id: str = Field(min_length=3, max_length=500)
    health_observation_refs: list[str] = Field(min_length=1)
    contract_health_refs: list[str] = Field(min_length=1)
    provenance_gap_refs: list[str] = Field(default_factory=list)
    drift_baseline_refs: list[str] = Field(min_length=1)
    drift_refs: list[str] = Field(min_length=1)
    stale_signal_refs: list[str] = Field(default_factory=list)
    federation_policy_drift_refs: list[str] = Field(default_factory=list)
    slo_indicator_refs: list[str] = Field(min_length=1)
    audit_event_refs: list[str] = Field(min_length=1)
    alert_refs: list[str] = Field(min_length=1)
    trace_refs: list[str] = Field(min_length=1)
    as_of: str = Field(min_length=10, max_length=80)
    immutable: Literal[True] = True
    supersedable: Literal[True] = True
    snapshot_is_not_truth_verdict: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_refs(self):
        for vals,label in ((self.health_observation_refs,"health_observation_refs"),(self.contract_health_refs,"contract_health_refs"),(self.provenance_gap_refs,"provenance_gap_refs"),(self.drift_baseline_refs,"drift_baseline_refs"),(self.drift_refs,"drift_refs"),(self.stale_signal_refs,"stale_signal_refs"),(self.federation_policy_drift_refs,"federation_policy_drift_refs"),(self.slo_indicator_refs,"slo_indicator_refs"),(self.audit_event_refs,"audit_event_refs"),(self.alert_refs,"alert_refs"),(self.trace_refs,"trace_refs")): _unique(vals,label)
        return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class UnifiedRuntimeObservabilityAuditDriftBundle(BaseModel):
    release: Literal["3.97.0"] = "3.97.0"
    contract: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    policies: list[ObservabilityPolicy] = Field(min_length=1)
    health_observations: list[RuntimeHealthObservation] = Field(min_length=1)
    contract_health: list[ContractHealthObservation] = Field(min_length=1)
    audit_events: list[RuntimeAuditEvent] = Field(min_length=1)
    provenance_gaps: list[ProvenanceGapSignal] = Field(default_factory=list)
    drift_baselines: list[DriftBaseline] = Field(min_length=1)
    drift_observations: list[DriftObservation] = Field(min_length=1)
    stale_evidence_signals: list[StaleEvidenceSignal] = Field(default_factory=list)
    federation_policy_drift: list[FederationPolicyDriftSignal] = Field(default_factory=list)
    slo_indicators: list[RuntimeSLOIndicator] = Field(min_length=1)
    alerts: list[ObservabilityAlertDecision] = Field(min_length=1)
    traces: list[ObservabilityTrace] = Field(min_length=1)
    snapshots: list[ObservabilitySnapshot] = Field(min_length=1)
    database_migration: Literal["none"] = "none"

    @model_validator(mode="after")
    def validate_bundle(self):
        groups=[
            (self.policies,"policy_id"),(self.health_observations,"observation_id"),(self.contract_health,"contract_health_id"),(self.audit_events,"audit_event_id"),(self.provenance_gaps,"provenance_gap_id"),(self.drift_baselines,"baseline_id"),(self.drift_observations,"drift_id"),(self.stale_evidence_signals,"stale_signal_id"),(self.federation_policy_drift,"federation_policy_drift_id"),(self.slo_indicators,"slo_indicator_id"),(self.alerts,"alert_id"),(self.traces,"trace_id"),(self.snapshots,"snapshot_id")]
        for items,field in groups: _unique([getattr(x,field) for x in items],field)
        health={x.observation_id for x in self.health_observations}; contracts={x.contract_health_id for x in self.contract_health}; audits={x.audit_event_id for x in self.audit_events}; gaps={x.provenance_gap_id for x in self.provenance_gaps}; baselines={x.baseline_id for x in self.drift_baselines}; drifts={x.drift_id for x in self.drift_observations}; stale={x.stale_signal_id for x in self.stale_evidence_signals}; fed={x.federation_policy_drift_id for x in self.federation_policy_drift}; slo={x.slo_indicator_id for x in self.slo_indicators}; alerts={x.alert_id for x in self.alerts}; traces={x.trace_id for x in self.traces}
        for d in self.drift_observations:
            if d.baseline_ref not in baselines: raise ValueError("drift baseline unresolved")
        signal_ids=health|contracts|gaps|drifts|stale|fed|slo
        for a in self.alerts:
            if not set(a.signal_refs)<=signal_ids: raise ValueError("alert signal reference unresolved")
        for t in self.traces:
            if not set(t.observation_refs)<=signal_ids or not set(t.audit_event_refs)<=audits or not set(t.alert_refs)<=alerts: raise ValueError("trace references unresolved")
        for s in self.snapshots:
            if not set(s.health_observation_refs)<=health or not set(s.contract_health_refs)<=contracts or not set(s.provenance_gap_refs)<=gaps or not set(s.drift_baseline_refs)<=baselines or not set(s.drift_refs)<=drifts or not set(s.stale_signal_refs)<=stale or not set(s.federation_policy_drift_refs)<=fed or not set(s.slo_indicator_refs)<=slo or not set(s.audit_event_refs)<=audits or not set(s.alert_refs)<=alerts or not set(s.trace_refs)<=traces: raise ValueError("snapshot references unresolved")
        return self
    def fingerprint(self) -> str: return canonical_sha256(self)


def _h(label: str) -> str:
    import hashlib
    return hashlib.sha256(label.encode()).hexdigest()


@lru_cache(maxsize=1)
def reference_unified_runtime_observability_audit_drift_bundle() -> UnifiedRuntimeObservabilityAuditDriftBundle:
    governance=reference_federation_governance_trust_policy_bundle()
    policy=ObservabilityPolicy(policy_id="observability-default-v1")
    contracts=[V390_CONTRACT,V391_CONTRACT,V392_CONTRACT,V393_CONTRACT,V394_CONTRACT,V395_CONTRACT,V396_CONTRACT]
    health=[]
    for i,(cap,contract,state,latency) in enumerate([
        ("unified-entity-evidence-runtime",V390_CONTRACT,"healthy",41.0),
        ("runtime-policy-negotiation",V391_CONTRACT,"healthy",19.0),
        ("entity-evidence-query",V392_CONTRACT,"degraded",212.0),
        ("investigation-session",V393_CONTRACT,"healthy",33.0),
        ("cross-product-handoff",V394_CONTRACT,"healthy",47.0),
        ("federation-governance",V396_CONTRACT,"healthy",52.0),
    ],1):
        health.append(RuntimeHealthObservation(observation_id=f"health-{i:02d}",capability=cap,contract=contract,endpoint=f"/public/v1/{cap}/contract",state=state,latency_ms=latency,observed_at=f"2026-10-01T04:{i:02d}:00Z",source="platform-core-observer"))
    contract_health=[]
    for i,contract in enumerate([V390_CONTRACT,V395_CONTRACT,V396_CONTRACT],1):
        expected=_h(contract+"|expected"); observed=expected if i!=2 else _h(contract+"|observed-qualified-change")
        contract_health.append(ContractHealthObservation(contract_health_id=f"contract-health-{i:02d}",contract=contract,expected_version="v1",observed_version="v1",schema_fingerprint_expected=expected,schema_fingerprint_observed=observed,compatible=(i!=2),observed_at=f"2026-10-01T04:1{i}:00Z"))
    audits=[]
    audit_specs=[
        ("health-check","health-03"),("contract-check","contract-health-02"),("provenance-check","gap-01"),("drift-evaluation","drift-02"),("freshness-check","stale-01"),("federation-policy-check","fed-drift-01"),("slo-evaluation","slo-02"),("alert-decision","alert-03")]
    for i,(et,target) in enumerate(audit_specs,1):
        audits.append(RuntimeAuditEvent(audit_event_id=f"audit-obs-{i:02d}",event_type=et,actor_or_runtime="platform-core-observer",target_ref=target,related_refs=[target],recorded_at=f"2026-10-01T04:{20+i:02d}:00Z",deterministic_event_sha256=_h(f"{et}|{target}|{i}")))
    gaps=[
        ProvenanceGapSignal(provenance_gap_id="gap-01",target_object_ref="query-result-remote-reference",expected_provenance_kind="local-validation-record",missing_or_incomplete_refs=["local-validation-record"],detected_at="2026-10-01T04:31:00Z",severity="moderate"),
        ProvenanceGapSignal(provenance_gap_id="gap-02",target_object_ref="runtime-output-derived-001",expected_provenance_kind="execution-attestation",missing_or_incomplete_refs=["attestation-reference"],detected_at="2026-10-01T04:32:00Z",severity="low"),
    ]
    baselines=[
        DriftBaseline(baseline_id="baseline-runtime-latency",drift_kind="runtime",target_ref="entity-evidence-query",metric_name="latency_ms",baseline_value=80.0,tolerance_absolute=60.0,established_at="2026-09-30T00:00:00Z",provenance_refs=["baseline-run-001"]),
        DriftBaseline(baseline_id="baseline-model-calibration",drift_kind="model",target_ref="linkage-model-reference",metric_name="calibration_error",baseline_value=0.04,tolerance_absolute=0.03,established_at="2026-09-30T00:00:00Z",provenance_refs=["model-eval-001"]),
        DriftBaseline(baseline_id="baseline-provenance-completeness",drift_kind="provenance",target_ref="investigation-session-reference",metric_name="provenance_completeness",baseline_value=1.0,tolerance_absolute=0.05,established_at="2026-09-30T00:00:00Z",provenance_refs=["session-checkpoint-001"]),
    ]
    drifts=[
        DriftObservation(drift_id="drift-01",baseline_ref="baseline-runtime-latency",drift_kind="runtime",target_ref="entity-evidence-query",observed_value=212.0,delta_absolute=132.0,outside_tolerance=True,severity="high",observed_at="2026-10-01T04:35:00Z",evidence_refs=["health-03"]),
        DriftObservation(drift_id="drift-02",baseline_ref="baseline-model-calibration",drift_kind="model",target_ref="linkage-model-reference",observed_value=0.09,delta_absolute=0.05,outside_tolerance=True,severity="moderate",observed_at="2026-10-01T04:36:00Z",evidence_refs=["model-eval-002"]),
        DriftObservation(drift_id="drift-03",baseline_ref="baseline-provenance-completeness",drift_kind="provenance",target_ref="investigation-session-reference",observed_value=0.92,delta_absolute=0.08,outside_tolerance=True,severity="moderate",observed_at="2026-10-01T04:37:00Z",evidence_refs=["gap-01","gap-02"]),
        DriftObservation(drift_id="drift-04",baseline_ref="baseline-runtime-latency",drift_kind="runtime",target_ref="cross-product-handoff",observed_value=96.0,delta_absolute=16.0,outside_tolerance=False,severity="informational",observed_at="2026-10-01T04:38:00Z",evidence_refs=["health-05"]),
        DriftObservation(drift_id="drift-05",baseline_ref="baseline-model-calibration",drift_kind="model",target_ref="secondary-model-reference",observed_value=0.05,delta_absolute=0.01,outside_tolerance=False,severity="informational",observed_at="2026-10-01T04:39:00Z",evidence_refs=["model-eval-003"]),
    ]
    stale=[
        StaleEvidenceSignal(stale_signal_id="stale-01",evidence_ref="documentary-source-reference-001",last_validated_at="2026-06-01T00:00:00Z",freshness_policy_days=90,age_days=122,stale=True,detected_at="2026-10-01T04:40:00Z"),
        StaleEvidenceSignal(stale_signal_id="stale-02",evidence_ref="documentary-source-reference-002",last_validated_at="2026-09-20T00:00:00Z",freshness_policy_days=90,age_days=11,stale=False,detected_at="2026-10-01T04:40:00Z"),
    ]
    fed_decision=governance.decisions[0]
    fed=[FederationPolicyDriftSignal(federation_policy_drift_id="fed-drift-01",node_ref=fed_decision.node_ref,policy_ref=fed_decision.policy_ref,previous_decision_ref=fed_decision.decision_id,current_state="node-now-constrained-reference-only",drift_kind="permission-change",detected_at="2026-10-01T04:41:00Z")]
    slo=[
        RuntimeSLOIndicator(slo_indicator_id="slo-01",service_or_capability="platform-core",metric_name="availability",objective=0.999,observed=0.9995,compliant=True,window="24h",observed_at="2026-10-01T04:42:00Z"),
        RuntimeSLOIndicator(slo_indicator_id="slo-02",service_or_capability="entity-evidence-query",metric_name="p95_latency_ms",objective=150.0,observed=212.0,compliant=False,window="1h",observed_at="2026-10-01T04:42:00Z"),
        RuntimeSLOIndicator(slo_indicator_id="slo-03",service_or_capability="federation-governance",metric_name="policy_decision_success",objective=0.99,observed=1.0,compliant=True,window="24h",observed_at="2026-10-01T04:42:00Z"),
        RuntimeSLOIndicator(slo_indicator_id="slo-04",service_or_capability="cross-product-handoff",metric_name="handoff_integrity",objective=1.0,observed=1.0,compliant=True,window="24h",observed_at="2026-10-01T04:42:00Z"),
    ]
    alerts=[
        ObservabilityAlertDecision(alert_id="alert-01",signal_refs=["drift-01","slo-02"],severity="high",disposition="investigate",rationale="Query latency exceeded both drift tolerance and SLO; investigate runtime performance without changing evidence state.",decided_at="2026-10-01T04:45:00Z",requires_review=True),
        ObservabilityAlertDecision(alert_id="alert-02",signal_refs=["gap-01","drift-03"],severity="moderate",disposition="investigate",rationale="Provenance completeness dropped below baseline; require provenance repair before promotion.",decided_at="2026-10-01T04:46:00Z",requires_review=True),
        ObservabilityAlertDecision(alert_id="alert-03",signal_refs=["stale-01"],severity="moderate",disposition="observe",rationale="Evidence exceeded freshness window; schedule revalidation, do not delete or mark false.",decided_at="2026-10-01T04:47:00Z",requires_review=True),
        ObservabilityAlertDecision(alert_id="alert-04",signal_refs=["fed-drift-01","contract-health-02"],severity="moderate",disposition="quarantine-runtime-output",rationale="Federation permission and attestation contract state changed; quarantine new remote-derived runtime output pending validation.",decided_at="2026-10-01T04:48:00Z",requires_review=True),
    ]
    all_signal_refs=[x.observation_id for x in health]+[x.contract_health_id for x in contract_health]+[x.provenance_gap_id for x in gaps]+[x.drift_id for x in drifts]+[x.stale_signal_id for x in stale]+[x.federation_policy_drift_id for x in fed]+[x.slo_indicator_id for x in slo]
    trace=ObservabilityTrace(trace_id="observability-trace-001",observation_refs=all_signal_refs,audit_event_refs=[x.audit_event_id for x in audits],alert_refs=[x.alert_id for x in alerts],started_at="2026-10-01T04:00:00Z",completed_at="2026-10-01T04:50:00Z")
    snapshot=ObservabilitySnapshot(snapshot_id="observability-snapshot-001",health_observation_refs=[x.observation_id for x in health],contract_health_refs=[x.contract_health_id for x in contract_health],provenance_gap_refs=[x.provenance_gap_id for x in gaps],drift_baseline_refs=[x.baseline_id for x in baselines],drift_refs=[x.drift_id for x in drifts],stale_signal_refs=[x.stale_signal_id for x in stale],federation_policy_drift_refs=[x.federation_policy_drift_id for x in fed],slo_indicator_refs=[x.slo_indicator_id for x in slo],audit_event_refs=[x.audit_event_id for x in audits],alert_refs=[x.alert_id for x in alerts],trace_refs=[trace.trace_id],as_of="2026-10-01T04:50:00Z")
    return UnifiedRuntimeObservabilityAuditDriftBundle(policies=[policy],health_observations=health,contract_health=contract_health,audit_events=audits,provenance_gaps=gaps,drift_baselines=baselines,drift_observations=drifts,stale_evidence_signals=stale,federation_policy_drift=fed,slo_indicators=slo,alerts=alerts,traces=[trace],snapshots=[snapshot])


def contract_document() -> dict[str, Any]:
    b=reference_unified_runtime_observability_audit_drift_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "upstream_contracts": [V390_CONTRACT,V391_CONTRACT,V392_CONTRACT,V393_CONTRACT,V394_CONTRACT,V395_CONTRACT,V396_CONTRACT],
        "principles": {
            "observability_is_diagnostic_not_epistemic": True,
            "runtime_health_is_separate_from_claim_truth": True,
            "contract_health_is_versioned_and_auditable": True,
            "provenance_gaps_are_explicit": True,
            "drift_requires_explicit_baselines": True,
            "stale_evidence_requires_revalidation_not_deletion": True,
            "federation_policy_drift_is_preserved": True,
            "slo_breaches_are_operational_signals": True,
            "audit_events_are_immutable": True,
            "alerts_are_provenance_bearing": True,
        },
        "boundaries": {
            "anomaly_establishes_claim_false": False,
            "drift_establishes_claim_false": False,
            "failed_health_check_invalidates_evidence": False,
            "stale_evidence_is_false": False,
            "contract_mismatch_invalidates_historical_objects": False,
            "alert_promotes_or_demotes_epistemic_state": False,
            "observability_resolves_contradictions": False,
            "observability_deletes_evidence": False,
            "identity_graph_mutation_performed": False,
            "relationship_graph_mutation_performed": False,
            "evidence_graph_mutation_performed": False,
        },
        "reference": {
            "health_observations": len(b.health_observations),
            "contract_health": len(b.contract_health),
            "audit_events": len(b.audit_events),
            "provenance_gaps": len(b.provenance_gaps),
            "drift_baselines": len(b.drift_baselines),
            "drift_observations": len(b.drift_observations),
            "stale_evidence_signals": len(b.stale_evidence_signals),
            "federation_policy_drift": len(b.federation_policy_drift),
            "slo_indicators": len(b.slo_indicators),
            "alerts": len(b.alerts),
            "traces": len(b.traces),
            "snapshots": len(b.snapshots),
            "out_of_tolerance_drifts": sum(x.outside_tolerance for x in b.drift_observations),
            "slo_breaches": sum(not x.compliant for x in b.slo_indicators),
            "bundle_fingerprint_sha256": b.fingerprint(),
        },
        "database_migration": "none",
    }
