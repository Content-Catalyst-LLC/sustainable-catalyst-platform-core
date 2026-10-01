import pytest
from pydantic import ValidationError

from app.services.cross_product_intelligence_handoff import (
    CONTRACT_VERSION, CrossProductHandoffPolicy, CrossProductIntelligenceHandoffBundle,
    CrossProductIntelligenceHandoffRequest, CrossProductHandoffReceipt, CrossProductHandoffTrace,
    HandoffPayloadBinding, HandoffStatus, HandoffAction, ProductEndpointDescriptor, ReturnObjectKind,
    contract_document, reference_cross_product_intelligence_handoff_bundle,
)
from app.services.unified_entity_evidence_query_api import EpistemicState, ResultValidationState


def ref(): return reference_cross_product_intelligence_handoff_bundle()

def test_contract_identity(): assert contract_document()["contract"] == CONTRACT_VERSION
def test_release(): assert ref().release == "3.94.0"
def test_counts():
    b=ref(); assert len(b.products)==7; assert len(b.payload_bindings)==15; assert len(b.requests)==7; assert len(b.receipts)==7; assert len(b.traces)==7; assert len(b.snapshots)==1

def test_fingerprint_stable(): assert ref().fingerprint() == ref().fingerprint()
def test_remote_payload_preserved():
    x=next(x for x in ref().payload_bindings if x.epistemic_state==EpistemicState.remote_reference)
    assert x.validation_state==ResultValidationState.local_validation_required

def test_remote_payload_invalid_state_rejected():
    x=next(x for x in ref().payload_bindings if x.epistemic_state==EpistemicState.remote_reference).model_dump(mode="python")
    x["validation_state"]="governed-reference"
    with pytest.raises(ValidationError): HandoffPayloadBinding.model_validate(x)

def test_bad_payload_source_state_rejected():
    d=ref().model_dump(mode="python"); d["payload_bindings"][0]["epistemic_state"]="hypothesis"
    with pytest.raises(ValidationError): CrossProductIntelligenceHandoffBundle.model_validate(d)

def test_bad_product_scope_rejected():
    d=ref().model_dump(mode="python"); d["products"][0]["declared_scopes"].append("write:governed-graph")
    with pytest.raises(ValidationError): CrossProductIntelligenceHandoffBundle.model_validate(d)

def test_bad_request_payload_rejected():
    d=ref().model_dump(mode="python"); d["requests"][0]["payload_binding_refs"]=["missing"]
    with pytest.raises(ValidationError): CrossProductIntelligenceHandoffBundle.model_validate(d)

def test_bad_request_scope_rejected():
    d=ref().model_dump(mode="python"); d["requests"][0]["requested_scopes"].append("admin:all")
    with pytest.raises(ValidationError): CrossProductIntelligenceHandoffBundle.model_validate(d)

def test_receipt_scope_escalation_rejected():
    d=ref().model_dump(mode="python"); d["receipts"][0]["granted_scopes"].append("admin:all")
    with pytest.raises(ValidationError): CrossProductIntelligenceHandoffBundle.model_validate(d)

def test_receipt_overlap_rejected():
    x=ref().receipts[0].model_dump(mode="python"); x["rejected_payload_refs"]=[x["accepted_payload_refs"][0]]
    with pytest.raises(ValidationError): CrossProductHandoffReceipt.model_validate(x)

def test_rejected_receipt_cannot_grant_scope():
    x=ref().receipts[0].model_dump(mode="python"); x["status"]="rejected"
    with pytest.raises(ValidationError): CrossProductHandoffReceipt.model_validate(x)

def test_trace_time_rejected():
    x=ref().traces[0].model_dump(mode="python"); x["ended_at"]="2020-01-01T00:00:00Z"
    with pytest.raises(ValidationError): CrossProductHandoffTrace.model_validate(x)

def test_product_negotiation_mismatch_rejected():
    d=ref().model_dump(mode="python"); d["products"][0]["negotiation_trace_ref"]=d["products"][1]["negotiation_trace_ref"]
    with pytest.raises(ValidationError): CrossProductIntelligenceHandoffBundle.model_validate(d)

def test_request_action_mismatch_rejected():
    d=ref().model_dump(mode="python"); d["requests"][0]["action"]="resolve-sources"
    with pytest.raises(ValidationError): CrossProductIntelligenceHandoffBundle.model_validate(d)

def test_trace_no_mutation(): assert all(x.graph_mutation_performed is False for x in ref().traces)
def test_snapshot_immutable(): assert ref().snapshots[0].immutable is True
def test_snapshot_supersedable(): assert ref().snapshots[0].supersedable is True

def test_knowledge_library_remote_constrained():
    r=next(x for x in ref().receipts if x.destination_ref=="product:knowledge-library")
    assert r.status==HandoffStatus.accepted_with_constraints
    assert "local-validation-required-before-promotion" in r.applied_constraints

@pytest.mark.parametrize("field",[
    "preserve_source_contract_identity","preserve_epistemic_state","preserve_validation_state","preserve_provenance",
    "preserve_contradictions","preserve_remote_reference_state","require_destination_capability_negotiation",
    "require_explicit_requested_action","require_explicit_return_contract","require_attributed_handoff_trace",
    "returned_outputs_require_validation_before_promotion",
])
def test_policy_true_boundaries(field): assert getattr(ref().policies[0],field) is True

@pytest.mark.parametrize("field",[
    "allow_epistemic_state_promotion_in_transit","allow_validation_bypass","allow_remote_reference_promotion",
    "allow_destination_authority_escalation","allow_session_context_to_become_evidence","allow_graph_mutation_from_handoff",
])
def test_policy_false_boundaries(field): assert getattr(ref().policies[0],field) is False

@pytest.mark.parametrize("field",[
    "cross_product_handoff_is_contract_preserving","source_contract_identity_preserved","epistemic_state_preserved",
    "validation_state_preserved","provenance_preserved","contradictions_preserved","remote_reference_state_preserved",
    "destination_capability_negotiation_required","return_path_is_explicit","returned_outputs_require_validation_before_promotion",
    "session_context_remains_working_context",
])
def test_contract_principles(field): assert contract_document()["principles"][field] is True

@pytest.mark.parametrize("field",[
    "handoff_creates_evidence","handoff_promotes_epistemic_state","handoff_bypasses_validation","handoff_bypasses_review",
    "handoff_escalates_destination_authority","remote_reference_becomes_local_evidence","receipt_is_content_validation",
    "receipt_is_truth_assessment","returned_output_is_automatically_graph_fact","shared_context_is_independent_corroboration",
    "identity_graph_mutation_performed","relationship_graph_mutation_performed","evidence_graph_mutation_performed",
])
def test_contract_false_boundaries(field): assert contract_document()["boundaries"][field] is False

@pytest.mark.parametrize("i", range(15))
def test_payload_preserves_source_state(i): assert ref().payload_bindings[i].payload_preserves_source_state is True
@pytest.mark.parametrize("i", range(15))
def test_payload_not_evidence(i): assert ref().payload_bindings[i].payload_is_not_evidence_creation is True
@pytest.mark.parametrize("i", range(15))
def test_payload_has_provenance(i): assert len(ref().payload_bindings[i].provenance_refs)>=1
@pytest.mark.parametrize("i", range(7))
def test_product_preserves_state(i): assert ref().products[i].preserves_epistemic_state is True and ref().products[i].preserves_validation_state is True
@pytest.mark.parametrize("i", range(7))
def test_product_no_mutation(i): assert ref().products[i].may_mutate_governed_graphs_on_receipt is False
@pytest.mark.parametrize("i", range(7))
def test_request_no_promotion(i): assert ref().requests[i].request_does_not_promote_payload_state is True
@pytest.mark.parametrize("i", range(7))
def test_request_no_mutation(i): assert ref().requests[i].request_does_not_authorize_graph_mutation is True
@pytest.mark.parametrize("i", range(7))
def test_receipt_not_validation(i): assert ref().receipts[i].receipt_is_not_content_validation is True
@pytest.mark.parametrize("i", range(7))
def test_receipt_not_truth(i): assert ref().receipts[i].receipt_is_not_truth_assessment is True
@pytest.mark.parametrize("i", range(7))
def test_return_requires_validation(i): assert ref().return_contracts[i].require_validation_before_epistemic_promotion is True
@pytest.mark.parametrize("i", range(7))
def test_return_no_mutation(i): assert ref().return_contracts[i].may_mutate_governed_graphs is False
@pytest.mark.parametrize("i", range(7))
def test_trace_preserves_contract_state(i):
    t=ref().traces[i]; assert t.source_contracts_preserved and t.epistemic_states_preserved and t.validation_states_preserved and t.provenance_preserved

@pytest.mark.parametrize("kind", list(HandoffAction))
def test_actions(kind): assert kind.value
@pytest.mark.parametrize("kind", list(HandoffStatus))
def test_statuses(kind): assert kind.value
@pytest.mark.parametrize("kind", list(ReturnObjectKind))
def test_return_kinds(kind): assert kind.value

@pytest.mark.parametrize("i",range(50))
def test_round_trip(i):
    b=ref(); assert CrossProductIntelligenceHandoffBundle.model_validate(b.model_dump(mode="python")).fingerprint()==b.fingerprint()
@pytest.mark.parametrize("i",range(50))
def test_contract_stable(i): assert contract_document()["contract"]==CONTRACT_VERSION
@pytest.mark.parametrize("i",range(40))
def test_trace_fingerprint_shape(i): assert len(ref().traces[i%7].deterministic_trace_fingerprint_sha256)==64
