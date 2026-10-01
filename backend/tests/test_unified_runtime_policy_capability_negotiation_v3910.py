import pytest
from pydantic import ValidationError
from app.services.unified_runtime_policy_capability_negotiation import (
    CORE_RELEASE, CONTRACT_VERSION, CapabilityAvailability, CompatibilityStatus, FallbackMode, ConsumerKind,
    RuntimeCapabilityDescriptor, ConsumerCapabilityRequirement, RuntimeConsumerProfile, RuntimeFallbackRule,
    CapabilityNegotiationDecision, UnifiedRuntimePolicyCapabilityNegotiationBundle,
    reference_unified_runtime_policy_capability_negotiation_bundle, contract_document,
)

def ref(): return reference_unified_runtime_policy_capability_negotiation_bundle()
def test_release(): assert CORE_RELEASE == "3.91.0"
def test_contract(): assert CONTRACT_VERSION == "sc.core.unified-runtime-policy-capability-negotiation.v1"
def test_reference_valid(): assert ref().release == "3.91.0"
def test_counts():
    b=ref(); assert (len(b.capabilities),len(b.requirements),len(b.consumers),len(b.policies),len(b.fallback_rules),len(b.decisions),len(b.traces),len(b.snapshots)) == (14,17,7,1,1,17,7,1)
def test_degraded_count(): assert sum(x.availability==CapabilityAvailability.degraded for x in ref().capabilities)==1
def test_degraded_is_federation(): assert next(x for x in ref().capabilities if x.availability==CapabilityAvailability.degraded).release=="3.89.0"
def test_no_graph_mutation():
    b=ref(); assert not b.identity_graph_mutation_performed and not b.relationship_graph_mutation_performed and not b.evidence_graph_mutation_performed
def test_fingerprint_stable(): assert ref().fingerprint()==ref().fingerprint()
def test_contract_fingerprint(): assert contract_document()["reference"]["bundle_fingerprint_sha256"]==ref().fingerprint()
def test_consumer_kinds_complete(): assert {x.consumer_kind for x in ref().consumers}=={ConsumerKind.workspace,ConsumerKind.knowledge_library,ConsumerKind.research_librarian,ConsumerKind.research_lab,ConsumerKind.workbench,ConsumerKind.site_intelligence,ConsumerKind.decision_studio}
def test_federation_decision_degraded(): assert next(x for x in ref().decisions if x.capability_ref=="runtime-capability:3890").status==CompatibilityStatus.degraded
def test_federation_fallback_reference_only(): assert ref().fallback_rules[0].mode==FallbackMode.reference_only
def test_library_trace_degraded(): assert next(x for x in ref().traces if x.consumer_ref=="consumer:knowledge-library").final_status==CompatibilityStatus.degraded

def test_unknown_cap_dependency_rejected():
    d=ref().model_dump(mode="python"); d["capabilities"][1]["dependency_refs"]=["runtime-capability:missing"]
    with pytest.raises(ValidationError): UnifiedRuntimePolicyCapabilityNegotiationBundle.model_validate(d)
def test_unknown_requirement_cap_rejected():
    d=ref().model_dump(mode="python"); d["requirements"][0]["capability_ref"]="runtime-capability:missing"
    with pytest.raises(ValidationError): UnifiedRuntimePolicyCapabilityNegotiationBundle.model_validate(d)
def test_requirement_contract_mismatch_rejected():
    d=ref().model_dump(mode="python"); d["requirements"][0]["required_contract"]="wrong.contract"
    with pytest.raises(ValidationError): UnifiedRuntimePolicyCapabilityNegotiationBundle.model_validate(d)
def test_unknown_consumer_requirement_rejected():
    d=ref().model_dump(mode="python"); d["consumers"][0]["requirement_refs"].append("requirement:missing")
    with pytest.raises(ValidationError): UnifiedRuntimePolicyCapabilityNegotiationBundle.model_validate(d)
def test_unknown_fallback_capability_rejected():
    d=ref().model_dump(mode="python"); d["fallback_rules"][0]["capability_ref"]="runtime-capability:missing"
    with pytest.raises(ValidationError): UnifiedRuntimePolicyCapabilityNegotiationBundle.model_validate(d)
def test_unknown_decision_consumer_rejected():
    d=ref().model_dump(mode="python"); d["decisions"][0]["consumer_ref"]="consumer:missing"
    with pytest.raises(ValidationError): UnifiedRuntimePolicyCapabilityNegotiationBundle.model_validate(d)
def test_decision_requirement_mismatch_rejected():
    d=ref().model_dump(mode="python"); d["decisions"][0]["requirement_ref"]=d["consumers"][1]["requirement_refs"][0]
    with pytest.raises(ValidationError): UnifiedRuntimePolicyCapabilityNegotiationBundle.model_validate(d)
def test_scope_escalation_rejected():
    d=ref().model_dump(mode="python"); d["decisions"][0]["granted_scopes"].append("admin:everything")
    with pytest.raises(ValidationError): UnifiedRuntimePolicyCapabilityNegotiationBundle.model_validate(d)
def test_degraded_decision_needs_fallback():
    d=next(x for x in ref().decisions if x.status==CompatibilityStatus.degraded).model_dump(mode="python"); d["fallback_ref"]=None
    with pytest.raises(ValidationError): CapabilityNegotiationDecision.model_validate(d)
def test_rejected_decision_no_scopes():
    d=ref().decisions[0].model_dump(mode="python"); d["status"]="rejected"; d["granted_scopes"]=["read:provenance"]
    with pytest.raises(ValidationError): CapabilityNegotiationDecision.model_validate(d)
def test_trace_cross_consumer_decision_rejected():
    d=ref().model_dump(mode="python"); d["traces"][0]["decision_refs"].append(ref().traces[1].decision_refs[0])
    with pytest.raises(ValidationError): UnifiedRuntimePolicyCapabilityNegotiationBundle.model_validate(d)
def test_unknown_snapshot_trace_rejected():
    d=ref().model_dump(mode="python"); d["snapshots"][0]["trace_refs"].append("trace:missing")
    with pytest.raises(ValidationError): UnifiedRuntimePolicyCapabilityNegotiationBundle.model_validate(d)
def test_duplicate_capability_scope_rejected():
    d=ref().capabilities[0].model_dump(mode="python"); d["required_scopes"]=["read:provenance","read:provenance"]
    with pytest.raises(ValidationError): RuntimeCapabilityDescriptor.model_validate(d)
def test_duplicate_consumer_scope_rejected():
    d=ref().consumers[0].model_dump(mode="python"); d["declared_scopes"]=[d["declared_scopes"][0]]*2
    with pytest.raises(ValidationError): RuntimeConsumerProfile.model_validate(d)
def test_duplicate_requirement_scope_rejected():
    d=ref().requirements[0].model_dump(mode="python"); d["required_scopes"]=["read:provenance","read:provenance"]
    with pytest.raises(ValidationError): ConsumerCapabilityRequirement.model_validate(d)
def test_duplicate_fallback_trigger_rejected():
    d=ref().fallback_rules[0].model_dump(mode="python"); d["trigger_availability"]=["degraded","degraded"]
    with pytest.raises(ValidationError): RuntimeFallbackRule.model_validate(d)

@pytest.mark.parametrize("field",[
    "require_exact_contract_identity","enforce_minimum_release","grant_only_declared_scope_intersection",
    "preserve_upstream_epistemic_state","preserve_upstream_provenance","preserve_review_and_validation_gates",
    "require_explicit_degradation","require_explicit_fallback","require_auditable_decision_trace",
])
def test_policy_requirements(field): assert getattr(ref().policies[0],field) is True

@pytest.mark.parametrize("field",[
    "allow_scope_escalation","allow_boundary_weakening","allow_candidate_promotion","allow_hypothesis_promotion",
    "allow_local_validation_bypass","allow_human_review_bypass",
])
def test_policy_prohibitions(field): assert getattr(ref().policies[0],field) is False

@pytest.mark.parametrize("field",[
    "unified_control_plane_over_v3900_runtime","capability_discovery_is_descriptive_not_authoritative",
    "negotiation_preserves_upstream_contract_identity","negotiation_preserves_epistemic_state","negotiation_preserves_provenance",
    "minimum_release_requirements_enforced","permission_scope_intersection_enforced","degradation_is_explicit",
    "fallbacks_reduce_or_preserve_authority_never_increase_it","consumer_compatibility_is_auditable",
    "negotiation_trace_is_reproducible","review_and_local_validation_gates_preserved",
])
def test_contract_principles(field): assert contract_document()["principles"][field] is True

@pytest.mark.parametrize("field",[
    "negotiation_grants_undeclared_scope","negotiation_weakens_epistemic_boundaries","negotiation_converts_candidate_to_fact",
    "negotiation_converts_hypothesis_to_evidence","negotiation_bypasses_local_validation","negotiation_bypasses_human_review",
    "degraded_mode_increases_authority","capability_availability_implies_truth","contract_compatibility_implies_content_truth",
    "identity_graph_mutation_performed","relationship_graph_mutation_performed","evidence_graph_mutation_performed",
])
def test_contract_boundaries(field): assert contract_document()["boundaries"][field] is False

@pytest.mark.parametrize("i", range(14))
def test_capability_preserves_contract(i): assert ref().capabilities[i].preserves_upstream_contract_identity is True
@pytest.mark.parametrize("i", range(14))
def test_capability_preserves_epistemic_state(i): assert ref().capabilities[i].preserves_epistemic_state is True
@pytest.mark.parametrize("i", range(14))
def test_capability_preserves_provenance(i): assert ref().capabilities[i].preserves_provenance is True
@pytest.mark.parametrize("i", range(14))
def test_capability_availability_not_truth(i): assert ref().capabilities[i].capability_availability_is_not_truth_signal is True
@pytest.mark.parametrize("i", range(14))
def test_capability_no_mutation(i): assert ref().capabilities[i].may_mutate_governed_graphs is False
@pytest.mark.parametrize("i", range(17))
def test_requirement_epistemic_preservation(i): assert ref().requirements[i].requires_epistemic_state_preservation is True
@pytest.mark.parametrize("i", range(17))
def test_requirement_provenance_preservation(i): assert ref().requirements[i].requires_provenance_preservation is True
@pytest.mark.parametrize("i", range(7))
def test_consumer_no_mutation(i): assert ref().consumers[i].no_graph_mutation_requested is True
@pytest.mark.parametrize("i", range(17))
def test_decision_contract_preserved(i): assert ref().decisions[i].contract_identity_preserved is True
@pytest.mark.parametrize("i", range(17))
def test_decision_release_satisfied(i): assert ref().decisions[i].release_requirement_satisfied is True
@pytest.mark.parametrize("i", range(17))
def test_decision_epistemic_preserved(i): assert ref().decisions[i].epistemic_boundaries_preserved is True
@pytest.mark.parametrize("i", range(17))
def test_decision_provenance_preserved(i): assert ref().decisions[i].provenance_preserved is True
@pytest.mark.parametrize("i", range(17))
def test_decision_review_gate_preserved(i): assert ref().decisions[i].review_gates_preserved is True
@pytest.mark.parametrize("i", range(17))
def test_decision_not_validation(i): assert ref().decisions[i].decision_is_not_content_validation is True
@pytest.mark.parametrize("i", range(17))
def test_decision_not_truth(i): assert ref().decisions[i].decision_is_not_truth_assessment is True
@pytest.mark.parametrize("i", range(7))
def test_trace_policy_not_weakened(i): assert ref().traces[i].trace_is_not_authorization_to_weaken_policy is True
@pytest.mark.parametrize("i", range(7))
def test_trace_not_validation(i): assert ref().traces[i].trace_is_not_content_validation is True
@pytest.mark.parametrize("i", range(7))
def test_trace_not_truth(i): assert ref().traces[i].trace_is_not_truth_assessment is True

def test_fallback_authority_not_increased(): assert ref().fallback_rules[0].fallback_may_not_increase_authority is True
def test_fallback_no_promotion(): assert ref().fallback_rules[0].fallback_may_not_promote_graph_fact is True
def test_fallback_provenance(): assert ref().fallback_rules[0].fallback_preserves_provenance is True
def test_snapshot_immutable(): assert ref().snapshots[0].immutable is True
def test_snapshot_not_authority(): assert ref().snapshots[0].snapshot_is_not_runtime_authority is True
def test_snapshot_availability_not_truth(): assert ref().snapshots[0].availability_state_is_not_truth_signal is True
def test_snapshot_supersedable(): assert ref().snapshots[0].later_capability_state_may_supersede_snapshot is True
@pytest.mark.parametrize("state", list(CapabilityAvailability))
def test_availability_enum(state): assert state.value
@pytest.mark.parametrize("state", list(CompatibilityStatus))
def test_compatibility_enum(state): assert state.value
@pytest.mark.parametrize("state", list(FallbackMode))
def test_fallback_enum(state): assert state.value
@pytest.mark.parametrize("state", list(ConsumerKind))
def test_consumer_enum(state): assert state.value
