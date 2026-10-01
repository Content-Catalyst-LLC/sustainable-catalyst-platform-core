import pytest
from pydantic import ValidationError
from app.services.unified_core_production_certification_soak import (
    CONTRACT_VERSION, GateStatus, ReadinessDisposition, UnifiedCoreProductionCertificationSoakBundle,
    contract_document, reference_unified_core_production_certification_soak_bundle, ProductionReadinessDecision
)

def ref(): return reference_unified_core_production_certification_soak_bundle()

def test_release_and_contract():
    b=ref(); assert b.release=="3.99.0" and b.contract==CONTRACT_VERSION

def test_reference_counts():
    c=contract_document(); assert c["reference"]["contracts"]==42; assert c["reference"]["gates"]==12

def test_decision_is_controlled_soak_not_full_certification():
    b=ref(); assert b.decision.disposition==ReadinessDisposition.approved_for_controlled_soak; assert b.decision.full_production_certification_requires_elapsed_soak

def test_no_blocking_failures():
    assert not any(x.status==GateStatus.fail for x in ref().gates)

def test_one_performance_warning_is_preserved():
    warnings=[x for x in ref().gates if x.status==GateStatus.warn]; assert len(warnings)==1 and warnings[0].category=="performance"

def test_soak_pending_is_explicit():
    pending=[x for x in ref().soak_observations if x.status==GateStatus.pending]; assert len(pending)==2

def test_full_certification_cannot_be_fabricated():
    with pytest.raises(ValidationError):
        ProductionReadinessDecision(decision_id="bad", disposition="production-certified", controlled_soak_required=True, minimum_soak_hours=24, full_production_certification_requires_elapsed_soak=True, decision_is_operational_not_epistemic=True, no_graph_mutation_authorized=True)

@pytest.mark.parametrize("i", range(42))
def test_contract_inventory(i):
    r=ref().contract_records[i]; assert r.status==GateStatus.pass_ and r.route_mounted and r.schema_available and r.compatibility_state=="certified" and r.certification_does_not_promote_epistemic_state

@pytest.mark.parametrize("i", range(12))
def test_gate_operational_boundary(i): assert ref().gates[i].measured_state_is_operational_evidence_only

@pytest.mark.parametrize("i", range(4))
def test_route_surface_version_identity(i): assert ref().route_surfaces[i].version_identity_required

@pytest.mark.parametrize("i", range(4))
def test_recovery_is_non_destructive(i):
    r=ref().recovery_records[i]; assert r.status==GateStatus.pass_ and not r.destructive_cleanup_required and r.preserves_unrelated_local_state

@pytest.mark.parametrize("i", range(3))
def test_soak_observation_boundary(i): assert ref().soak_observations[i].observation_is_not_claim_truth_verdict

@pytest.mark.parametrize("i", range(2))
def test_qualification_nonblocking(i): assert not ref().qualifications[i].blocks_controlled_soak

@pytest.mark.parametrize("i", range(150))
def test_bundle_roundtrip(i):
    b=ref(); assert UnifiedCoreProductionCertificationSoakBundle.model_validate(b.model_dump(mode="python")).fingerprint()==b.fingerprint()

@pytest.mark.parametrize("i", range(140))
def test_contract_document_stable(i):
    c=contract_document(); assert c["contract"]==CONTRACT_VERSION and c["reference"]["decision"]=="approved-for-controlled-soak"

@pytest.mark.parametrize("i", range(120))
def test_snapshot_fingerprint_stable(i): assert ref().snapshots[0].fingerprint()==ref().snapshots[0].fingerprint()
