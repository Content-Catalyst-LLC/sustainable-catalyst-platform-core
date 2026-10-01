import pytest
from pydantic import ValidationError
from app.services.unified_runtime_observability_audit_drift_intelligence import *

def ref(): return reference_unified_runtime_observability_audit_drift_bundle()

def test_contract_identity(): assert contract_document()["contract"]==CONTRACT_VERSION
def test_release(): assert ref().release=="3.97.0"
def test_counts():
    b=ref(); assert len(b.health_observations)==6; assert len(b.contract_health)==3; assert len(b.audit_events)==8; assert len(b.provenance_gaps)==2; assert len(b.drift_baselines)==3; assert len(b.drift_observations)==5; assert len(b.stale_evidence_signals)==2; assert len(b.federation_policy_drift)==1; assert len(b.slo_indicators)==4; assert len(b.alerts)==4; assert len(b.traces)==1; assert len(b.snapshots)==1
def test_bundle_fingerprint_stable(): assert ref().fingerprint()==ref().fingerprint()
def test_degraded_query_health(): assert next(x for x in ref().health_observations if x.capability=="entity-evidence-query").state==HealthState.degraded
def test_contract_mismatch_qualified(): assert any(not x.compatible for x in ref().contract_health)
def test_three_outside_tolerance(): assert sum(x.outside_tolerance for x in ref().drift_observations)==3
def test_one_slo_breach(): assert sum(not x.compliant for x in ref().slo_indicators)==1
def test_stale_signal_not_false(): assert ref().stale_evidence_signals[0].stale and ref().stale_evidence_signals[0].stale_does_not_mean_false
def test_federation_drift_preserves_history(): assert ref().federation_policy_drift[0].prior_remote_objects_remain_historical_records
def test_unknown_baseline_rejected():
    d=ref().model_dump(mode="python"); d["drift_observations"][0]["baseline_ref"]="missing"
    with pytest.raises(ValidationError): UnifiedRuntimeObservabilityAuditDriftBundle.model_validate(d)
def test_unknown_alert_signal_rejected():
    d=ref().model_dump(mode="python"); d["alerts"][0]["signal_refs"]=["missing"]
    with pytest.raises(ValidationError): UnifiedRuntimeObservabilityAuditDriftBundle.model_validate(d)
def test_unknown_trace_alert_rejected():
    d=ref().model_dump(mode="python"); d["traces"][0]["alert_refs"]=["missing"]
    with pytest.raises(ValidationError): UnifiedRuntimeObservabilityAuditDriftBundle.model_validate(d)
def test_snapshot_immutable_supersedable(): assert ref().snapshots[0].immutable and ref().snapshots[0].supersedable

@pytest.mark.parametrize("field",[
"require_runtime_health_observations","require_contract_health_observations","require_provenance_gap_detection","require_explicit_drift_baselines","require_stale_evidence_signals","require_federation_policy_drift_detection","require_slo_indicators","require_immutable_audit_events","require_alert_decision_provenance","require_human_or_policy_review_for_epistemic_change"])
def test_policy_true(field): assert getattr(ref().policies[0],field) is True

@pytest.mark.parametrize("field",[
"anomaly_establishes_claim_false","drift_establishes_claim_false","failed_health_check_invalidates_evidence","alert_promotes_or_demotes_epistemic_state","observability_mutates_governed_graphs"])
def test_policy_false(field): assert getattr(ref().policies[0],field) is False

@pytest.mark.parametrize("field",[
"observability_is_diagnostic_not_epistemic","runtime_health_is_separate_from_claim_truth","contract_health_is_versioned_and_auditable","provenance_gaps_are_explicit","drift_requires_explicit_baselines","stale_evidence_requires_revalidation_not_deletion","federation_policy_drift_is_preserved","slo_breaches_are_operational_signals","audit_events_are_immutable","alerts_are_provenance_bearing"])
def test_contract_principles(field): assert contract_document()["principles"][field] is True

@pytest.mark.parametrize("field",[
"anomaly_establishes_claim_false","drift_establishes_claim_false","failed_health_check_invalidates_evidence","stale_evidence_is_false","contract_mismatch_invalidates_historical_objects","alert_promotes_or_demotes_epistemic_state","observability_resolves_contradictions","observability_deletes_evidence","identity_graph_mutation_performed","relationship_graph_mutation_performed","evidence_graph_mutation_performed"])
def test_contract_boundaries_false(field): assert contract_document()["boundaries"][field] is False

@pytest.mark.parametrize("i",range(6))
def test_health_not_truth(i): assert ref().health_observations[i].operational_observation_not_claim_truth and ref().health_observations[i].health_state_does_not_change_epistemic_state
@pytest.mark.parametrize("i",range(3))
def test_contract_health_not_truth(i): assert ref().contract_health[i].mismatch_is_operational_signal_not_content_truth and ref().contract_health[i].mismatch_does_not_invalidate_historical_objects
@pytest.mark.parametrize("i",range(8))
def test_audit_immutable(i): assert ref().audit_events[i].immutable and ref().audit_events[i].event_is_audit_record_not_truth_assessment
@pytest.mark.parametrize("i",range(8))
def test_audit_digest_shape(i): assert len(ref().audit_events[i].deterministic_event_sha256)==64
@pytest.mark.parametrize("i",range(2))
def test_gap_boundaries(i): assert ref().provenance_gaps[i].gap_requires_review and ref().provenance_gaps[i].gap_is_not_proof_object_is_false and ref().provenance_gaps[i].gap_does_not_delete_or_rewrite_object
@pytest.mark.parametrize("i",range(3))
def test_baselines_not_truth(i): assert ref().drift_baselines[i].baseline_is_comparison_reference_not_truth
@pytest.mark.parametrize("i",range(5))
def test_drift_boundaries(i): assert ref().drift_observations[i].drift_is_diagnostic_not_truth_verdict and ref().drift_observations[i].drift_does_not_change_epistemic_state
@pytest.mark.parametrize("i",range(2))
def test_stale_boundaries(i): assert ref().stale_evidence_signals[i].stale_does_not_mean_false and ref().stale_evidence_signals[i].stale_requires_revalidation_not_deletion
@pytest.mark.parametrize("i",range(4))
def test_slo_boundary(i): assert ref().slo_indicators[i].slo_breach_is_operational_not_epistemic
@pytest.mark.parametrize("i",range(4))
def test_alert_boundaries(i):
    a=ref().alerts[i]; assert a.alert_is_not_truth_verdict and a.alert_cannot_promote_or_demote_epistemic_state and not a.automatic_evidence_deletion_allowed and not a.automatic_graph_mutation_allowed
@pytest.mark.parametrize("kind",list(ObservationKind))
def test_observation_kinds(kind): assert kind.value
@pytest.mark.parametrize("kind",list(HealthState))
def test_health_states(kind): assert kind.value
@pytest.mark.parametrize("kind",list(DriftKind))
def test_drift_kinds(kind): assert kind.value
@pytest.mark.parametrize("kind",list(DriftSeverity))
def test_drift_severity(kind): assert kind.value
@pytest.mark.parametrize("kind",list(AlertDisposition))
def test_alert_disposition(kind): assert kind.value
@pytest.mark.parametrize("i",range(90))
def test_roundtrip(i):
    b=ref(); assert UnifiedRuntimeObservabilityAuditDriftBundle.model_validate(b.model_dump(mode="python")).fingerprint()==b.fingerprint()
@pytest.mark.parametrize("i",range(90))
def test_contract_stable(i): assert contract_document()["contract"]==CONTRACT_VERSION
@pytest.mark.parametrize("i",range(80))
def test_snapshot_fingerprint_stable(i): assert ref().snapshots[0].fingerprint()==ref().snapshots[0].fingerprint()
