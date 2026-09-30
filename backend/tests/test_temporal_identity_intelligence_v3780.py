import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.routers import temporal_identity_intelligence as routes
from app.services.temporal_identity_intelligence import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    TemporalAssertionState,
    TemporalIdentifierAssertion,
    TemporalIdentityIntelligenceBundle,
    TemporalNameVariant,
    TemporalRoleTitleAssertion,
    TemporalSourceIdentityAssertion,
    contract_document,
    reference_temporal_identity_intelligence_bundle,
)


def ref():
    return reference_temporal_identity_intelligence_bundle()


def client():
    app = FastAPI()
    app.include_router(routes.router)
    app.include_router(routes.public_router)
    return TestClient(app)


def test_release(): assert CORE_RELEASE == "3.78.0"
def test_contract(): assert CONTRACT_VERSION == "sc.core.temporal-identity-alias-name-variant-intelligence.v1"
def test_extends_v3770(): assert contract_document()["extends_contract"] == "sc.core.entity-resolution-identity-graph-foundation.v1"
def test_three_names(): assert len(ref().temporal_names) == 3
def test_two_identifiers(): assert len(ref().temporal_identifiers) == 2
def test_two_roles(): assert len(ref().temporal_roles) == 2
def test_two_source_assertions(): assert len(ref().temporal_source_assertions) == 2
def test_one_conflict(): assert len(ref().temporal_conflicts) == 1
def test_one_snapshot(): assert len(ref().temporal_snapshots) == 1
def test_current_label_preserves_history(): assert ref().current_label_does_not_erase_historical_labels is True
def test_temporal_overlap_not_identity(): assert ref().temporal_overlap_does_not_establish_same_identity is True
def test_historical_role_not_current(): assert ref().historical_role_does_not_establish_current_affiliation is True
def test_context_cannot_auto_merge(): assert ref().temporal_context_cannot_auto_merge_entities is True
def test_former_name_bounded():
    x=ref().temporal_names[0]; assert x.valid_from and x.valid_to
def test_current_name_open_ended(): assert ref().temporal_names[1].valid_to is None
def test_disputed_name_preserved(): assert ref().temporal_names[2].state == TemporalAssertionState.disputed
def test_same_name_not_identity_proof(): assert all(x.same_name_across_time_is_not_identity_proof for x in ref().temporal_names)
def test_historical_name_not_current_fact(): assert all(x.historical_name_is_not_current_name_fact for x in ref().temporal_names)
def test_identifier_reuse_not_identity_proof(): assert all(x.identifier_reuse_is_not_identity_proof for x in ref().temporal_identifiers)
def test_expired_id_not_current_fact(): assert all(x.expired_identifier_is_not_current_identifier_fact for x in ref().temporal_identifiers)
def test_role_not_timeless_affiliation(): assert all(x.role_at_one_time_is_not_timeless_affiliation for x in ref().temporal_roles)
def test_title_not_current_authority(): assert all(x.title_does_not_establish_current_authority for x in ref().temporal_roles)
def test_source_assertion_not_canonical(): assert all(x.source_temporal_assertion_is_not_canonical_identity for x in ref().temporal_source_assertions)
def test_conflict_requires_review(): assert ref().temporal_conflicts[0].review_required is True
def test_conflict_does_not_auto_resolve(): assert ref().temporal_conflicts[0].conflict_does_not_auto_resolve is True
def test_conflicts_may_coexist(): assert ref().temporal_conflicts[0].conflicting_temporal_assertions_may_coexist is True
def test_snapshot_immutable(): assert ref().temporal_snapshots[0].immutable_snapshot is True
def test_snapshot_does_not_rewrite_history(): assert ref().temporal_snapshots[0].as_of_view_does_not_rewrite_historical_assertions is True
def test_snapshot_selection_not_resolution(): assert ref().temporal_snapshots[0].temporal_selection_is_not_identity_resolution is True
def test_reference_fingerprint_stable(): assert ref().fingerprint() == ref().fingerprint()
def test_contract_fingerprint_64(): assert len(contract_document()["reference"]["bundle_fingerprint_sha256"]) == 64
def test_bad_name_interval_rejected():
    d=ref().temporal_names[0].model_dump(); d["valid_from"]="2025-01-01T00:00:00Z"; d["valid_to"]="2024-01-01T00:00:00Z"
    with pytest.raises(ValidationError): TemporalNameVariant.model_validate(d)
def test_bad_identifier_interval_rejected():
    d=ref().temporal_identifiers[0].model_dump(); d["valid_from"]="2025-01-01T00:00:00Z"; d["valid_to"]="2024-01-01T00:00:00Z"
    with pytest.raises(ValidationError): TemporalIdentifierAssertion.model_validate(d)
def test_bad_role_interval_rejected():
    d=ref().temporal_roles[0].model_dump(); d["valid_from"]="2025-01-01T00:00:00Z"; d["valid_to"]="2024-01-01T00:00:00Z"
    with pytest.raises(ValidationError): TemporalRoleTitleAssertion.model_validate(d)
def test_bad_source_interval_rejected():
    d=ref().temporal_source_assertions[0].model_dump(); d["valid_from"]="2025-01-01T00:00:00Z"; d["valid_to"]="2024-01-01T00:00:00Z"
    with pytest.raises(ValidationError): TemporalSourceIdentityAssertion.model_validate(d)
def test_superseded_name_requires_reference():
    d=ref().temporal_names[0].model_dump(); d["superseded_by_name_ref"]=None
    with pytest.raises(ValidationError): TemporalNameVariant.model_validate(d)
def test_superseded_identifier_requires_reference():
    d=ref().temporal_identifiers[0].model_dump(); d["superseded_by_identifier_ref"]=None
    with pytest.raises(ValidationError): TemporalIdentifierAssertion.model_validate(d)
def test_unknown_name_entity_rejected():
    b=ref().model_copy(deep=True); b.temporal_names[0].entity_ref="entity:missing"
    with pytest.raises(ValidationError): TemporalIdentityIntelligenceBundle.model_validate(b.model_dump(mode="json"))
def test_unknown_identifier_entity_rejected():
    b=ref().model_copy(deep=True); b.temporal_identifiers[0].entity_ref="entity:missing"
    with pytest.raises(ValidationError): TemporalIdentityIntelligenceBundle.model_validate(b.model_dump(mode="json"))
def test_unknown_role_entity_rejected():
    b=ref().model_copy(deep=True); b.temporal_roles[0].entity_ref="entity:missing"
    with pytest.raises(ValidationError): TemporalIdentityIntelligenceBundle.model_validate(b.model_dump(mode="json"))
def test_unknown_source_entity_rejected():
    b=ref().model_copy(deep=True); b.temporal_source_assertions[0].entity_ref="entity:missing"
    with pytest.raises(ValidationError): TemporalIdentityIntelligenceBundle.model_validate(b.model_dump(mode="json"))
def test_unresolved_name_in_source_rejected():
    b=ref().model_copy(deep=True); b.temporal_source_assertions[0].temporal_name_refs=["temporal-name:missing"]
    with pytest.raises(ValidationError): TemporalIdentityIntelligenceBundle.model_validate(b.model_dump(mode="json"))
def test_unresolved_identifier_in_source_rejected():
    b=ref().model_copy(deep=True); b.temporal_source_assertions[0].temporal_identifier_refs=["temporal-id:missing"]
    with pytest.raises(ValidationError): TemporalIdentityIntelligenceBundle.model_validate(b.model_dump(mode="json"))
def test_unresolved_role_in_source_rejected():
    b=ref().model_copy(deep=True); b.temporal_source_assertions[0].temporal_role_refs=["temporal-role:missing"]
    with pytest.raises(ValidationError): TemporalIdentityIntelligenceBundle.model_validate(b.model_dump(mode="json"))
def test_unresolved_conflict_assertion_rejected():
    b=ref().model_copy(deep=True); b.temporal_conflicts[0].assertion_refs=[b.temporal_conflicts[0].assertion_refs[0],"missing:assertion"]
    with pytest.raises(ValidationError): TemporalIdentityIntelligenceBundle.model_validate(b.model_dump(mode="json"))
def test_unknown_graph_snapshot_rejected():
    b=ref().model_copy(deep=True); b.temporal_snapshots[0].identity_graph_snapshot_ref="snapshot:missing"
    with pytest.raises(ValidationError): TemporalIdentityIntelligenceBundle.model_validate(b.model_dump(mode="json"))
def test_unresolved_snapshot_name_rejected():
    b=ref().model_copy(deep=True); b.temporal_snapshots[0].active_temporal_name_refs=["temporal-name:missing"]
    with pytest.raises(ValidationError): TemporalIdentityIntelligenceBundle.model_validate(b.model_dump(mode="json"))
def test_public_contract_route():
    r=client().get("/public/v1/temporal-identity/contract"); assert r.status_code==200; assert r.json()["release"]=="3.78.0"
def test_private_contract_route():
    r=client().get("/v1/temporal-identity/contract"); assert r.status_code==200; assert r.json()["contract"]==CONTRACT_VERSION
def test_reference_route():
    r=client().get("/v1/temporal-identity/reference"); assert r.status_code==200; assert r.json()["ok"] is True
def test_validate_name_route():
    r=client().post("/v1/temporal-identity/validate-name",json=ref().temporal_names[0].model_dump(mode="json")); assert r.status_code==200
def test_validate_identifier_route():
    r=client().post("/v1/temporal-identity/validate-identifier",json=ref().temporal_identifiers[0].model_dump(mode="json")); assert r.status_code==200
def test_validate_role_route():
    r=client().post("/v1/temporal-identity/validate-role",json=ref().temporal_roles[0].model_dump(mode="json")); assert r.status_code==200
def test_validate_bundle_route():
    r=client().post("/v1/temporal-identity/validate-bundle",json=ref().model_dump(mode="json")); assert r.status_code==200
def test_contract_no_auto_conflict_resolution(): assert contract_document()["boundaries"]["core_auto_resolves_temporal_conflicts"] is False
def test_contract_no_auto_merge(): assert contract_document()["boundaries"]["core_auto_merges_entities_from_temporal_overlap"] is False
def test_contract_no_historical_rewrite(): assert contract_document()["boundaries"]["core_treats_current_name_as_historically_canonical"] is False
def test_contract_preserves_v3760_boundary(): assert contract_document()["roadmap_integration"]["preserves_v3760_evidence_validation_boundary"] is True
