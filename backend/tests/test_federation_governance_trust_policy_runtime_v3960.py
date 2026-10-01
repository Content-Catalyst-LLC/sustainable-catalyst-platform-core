import pytest
from pydantic import ValidationError
from app.services.federation_governance_trust_policy_runtime import *

def ref(): return reference_federation_governance_trust_policy_bundle()

def test_contract_identity(): assert contract_document()["contract"]==CONTRACT_VERSION
def test_release(): assert ref().release=="3.96.0"
def test_counts():
    b=ref(); assert len(b.nodes)==3; assert len(b.trust_scopes)==6; assert len(b.permissions)==6; assert len(b.actions)==1; assert len(b.intake_rules)==4; assert len(b.decisions)==3; assert len(b.conflicts)==1; assert len(b.audit_events)==7; assert len(b.snapshots)==1
def test_bundle_fingerprint_stable(): assert ref().fingerprint()==ref().fingerprint()
def test_revoked_node_denied():
    b=ref(); n=next(x for x in b.nodes if x.governance_state==GovernanceNodeState.revoked); d=next(x for x in b.decisions if x.node_ref==n.governed_node_id); assert d.disposition==GovernanceDecisionDisposition.denied
def test_peer_reference_only_decision(): assert any(x.disposition==GovernanceDecisionDisposition.reference_only for x in ref().decisions)
def test_conflict_preserved(): assert ref().conflicts[0].silent_overwrite_allowed is False and ref().conflicts[0].local_state_preserved and ref().conflicts[0].remote_state_preserved
def test_revoked_node_requires_exchange_revoked():
    d=ref().nodes[-1].model_dump(mode="python"); d["underlying_exchange_trust_state"]="authenticated"
    with pytest.raises(ValidationError): FederationGovernedNode.model_validate(d)
def test_duplicate_scope_contract_rejected():
    d=ref().trust_scopes[0].model_dump(mode="python"); d["allowed_contracts"]*=2
    with pytest.raises(ValidationError): FederationTrustScope.model_validate(d)
def test_unknown_scope_rejected():
    d=ref().model_dump(mode="python"); d["permissions"][0]["trust_scope_ref"]="missing"
    with pytest.raises(ValidationError): FederationGovernanceTrustPolicyBundle.model_validate(d)
def test_unknown_decision_node_rejected():
    d=ref().model_dump(mode="python"); d["decisions"][0]["node_ref"]="missing"
    with pytest.raises(ValidationError): FederationGovernanceTrustPolicyBundle.model_validate(d)
def test_snapshot_immutable_supersedable(): assert ref().snapshots[0].immutable and ref().snapshots[0].supersedable

def test_revocation_history_immutable(): assert ref().actions[0].historical_records_remain_immutable is True

@pytest.mark.parametrize("field",[
"require_registered_node_identity","require_current_node_state","require_scoped_trust","require_capability_permission","require_contract_allowlist","require_signature_verification_when_attested","require_local_validation_for_remote_content","require_conflict_preservation","require_explicit_revocation_and_suspension","require_auditable_policy_decisions"])
def test_policy_true(field): assert getattr(ref().policies[0],field) is True

@pytest.mark.parametrize("field",[
"allow_global_unscoped_trust","allow_trust_to_establish_content_truth","allow_signature_to_establish_content_truth","allow_policy_approval_to_create_local_evidence","allow_remote_content_to_bypass_local_validation","allow_conflict_overwrite","allow_suspended_node_to_exchange","allow_revoked_node_to_exchange","allow_policy_to_mutate_governed_graphs"])
def test_policy_false(field): assert getattr(ref().policies[0],field) is False

@pytest.mark.parametrize("field",[
"trust_is_scoped_not_global","node_state_is_revocable","capability_permissions_are_explicit","contract_allowlists_are_explicit","signature_verification_is_separate_from_content_truth","remote_content_requires_local_validation","conflicts_are_preserved","revocation_and_suspension_are_first_class","policy_decisions_are_auditable","historical_governance_records_are_immutable"])
def test_contract_principles(field): assert contract_document()["principles"][field] is True

@pytest.mark.parametrize("field",[
"global_unscoped_trust_allowed","trusted_node_establishes_content_truth","valid_signature_establishes_content_truth","policy_approval_creates_local_evidence","remote_content_bypasses_local_validation","federation_consensus_establishes_truth","conflict_silent_overwrite_allowed","suspended_node_may_exchange","revoked_node_may_exchange","governance_decision_promotes_epistemic_state","identity_graph_mutation_performed","relationship_graph_mutation_performed","evidence_graph_mutation_performed"])
def test_contract_false_boundaries(field): assert contract_document()["boundaries"][field] is False

@pytest.mark.parametrize("i",range(3))
def test_nodes_not_truth(i): assert ref().nodes[i].node_state_is_not_content_truth and ref().nodes[i].node_state_does_not_expand_content_authority
@pytest.mark.parametrize("i",range(6))
def test_scopes_require_local_validation(i): assert ref().trust_scopes[i].local_validation_required is True
@pytest.mark.parametrize("i",range(6))
def test_scopes_not_truth(i): assert ref().trust_scopes[i].trust_scope_is_not_truth_assessment and ref().trust_scopes[i].trust_scope_is_not_evidence_promotion
@pytest.mark.parametrize("i",range(6))
def test_permissions_not_truth(i): assert ref().permissions[i].permission_is_not_content_validation and ref().permissions[i].permission_is_not_truth_assessment
@pytest.mark.parametrize("i",range(6))
def test_permissions_no_authority_increase(i): assert ref().permissions[i].permission_cannot_increase_epistemic_authority is True
@pytest.mark.parametrize("i",range(4))
def test_intake_preserves_remote_state(i): assert ref().intake_rules[i].preserve_remote_epistemic_state and ref().intake_rules[i].preserve_remote_provenance and ref().intake_rules[i].require_local_validation
@pytest.mark.parametrize("i",range(3))
def test_decision_local_validation(i): assert ref().decisions[i].local_validation_required is True
@pytest.mark.parametrize("i",range(3))
def test_decisions_preserve_remote_state(i): assert ref().decisions[i].remote_epistemic_state_preserved and ref().decisions[i].remote_provenance_preserved
@pytest.mark.parametrize("i",range(3))
def test_decisions_not_truth(i): assert ref().decisions[i].decision_is_not_content_truth and ref().decisions[i].decision_is_not_local_evidence_promotion
@pytest.mark.parametrize("i",range(7))
def test_audit_digest_shape(i): assert len(ref().audit_events[i].deterministic_event_sha256)==64
@pytest.mark.parametrize("i",range(7))
def test_audit_not_truth(i): assert ref().audit_events[i].event_is_audit_record_not_truth_assessment is True
@pytest.mark.parametrize("kind",list(GovernanceNodeState))
def test_node_states(kind): assert kind.value
@pytest.mark.parametrize("kind",list(TrustScopeKind))
def test_scope_kinds(kind): assert kind.value
@pytest.mark.parametrize("kind",list(PermissionEffect))
def test_permission_effects(kind): assert kind.value
@pytest.mark.parametrize("kind",list(GovernanceDecisionDisposition))
def test_decision_dispositions(kind): assert kind.value
@pytest.mark.parametrize("i",range(80))
def test_roundtrip(i):
    b=ref(); assert FederationGovernanceTrustPolicyBundle.model_validate(b.model_dump(mode="python")).fingerprint()==b.fingerprint()
@pytest.mark.parametrize("i",range(80))
def test_contract_stable(i): assert contract_document()["contract"]==CONTRACT_VERSION
@pytest.mark.parametrize("i",range(60))
def test_snapshot_fingerprint_stable(i): assert ref().snapshots[0].fingerprint()==ref().snapshots[0].fingerprint()
