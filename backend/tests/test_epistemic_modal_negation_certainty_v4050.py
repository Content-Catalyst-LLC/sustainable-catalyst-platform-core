from copy import deepcopy

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.config import Settings
from app.main import create_app
from app.services.epistemic_modal_negation_certainty import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    EXTENDS_CONTRACTS,
    CertaintyLevel,
    EpistemicAssessment,
    EpistemicModalNegationCertaintyBundle,
    EpistemicReviewState,
    EpistemicSourceExcerpt,
    EpistemicState,
    ModalForce,
    Polarity,
    Proposition,
    contract_document,
    reference_epistemic_modal_negation_certainty_bundle,
)
from app.services.temporal_spatial_language_grounding import CONTRACT_VERSION as V44_CONTRACT


def ref():
    return reference_epistemic_modal_negation_certainty_bundle()


def payload():
    return ref().model_dump(mode="python")


def invalid(mutator):
    p = deepcopy(payload())
    mutator(p)
    with pytest.raises(ValidationError):
        EpistemicModalNegationCertaintyBundle.model_validate(p)


def test_release_identity():
    assert CORE_RELEASE == "4.5.0"
    assert CONTRACT_VERSION == "sc.core.epistemic-modal-negation-certainty-semantics.v1"
    version = tuple(int(x) for x in Settings().version.split("."))
    assert version >= (4, 5, 0)
    assert ref().release == "4.5.0"


def test_predecessor_is_v44_language_grounding():
    assert ref().predecessor_contract == V44_CONTRACT
    assert ref().temporal_spatial_grounding.release == "4.4.0"
    assert ref().temporal_spatial_grounding.contract == V44_CONTRACT


def test_dependency_order_is_governed():
    assert ref().extends_contracts == EXTENDS_CONTRACTS
    invalid(lambda p: p["extends_contracts"].reverse())


def test_reference_counts():
    c = contract_document()["reference"]
    assert c["source_excerpts"] == 1
    assert c["propositions"] == 4
    assert c["attributions"] == 3
    assert c["cues"] == 8
    assert c["negation_scopes"] == 1
    assert c["modal_scopes"] == 2
    assert c["conditional_scopes"] == 1
    assert c["assessments"] == 4
    assert c["negative_assessments"] == 1
    assert c["possible_modal_assessments"] == 2
    assert c["explicit_uncertainty_assessments"] == 1
    assert c["hypothetical_assessments"] == 1
    assert c["canonical_actor_bindings"] == 0


def test_source_excerpt_is_immutable_and_hashed():
    s = ref().source_excerpts[0]
    assert s.immutable is True
    assert s.source_excerpt_is_not_truth_validation is True
    assert s.content.startswith("The report states")
    assert len(s.content_sha256) == 64


def test_source_hash_mismatch_rejected():
    p = ref().source_excerpts[0].model_dump(mode="python")
    p["content"] += " altered"
    with pytest.raises(ValidationError):
        EpistemicSourceExcerpt.model_validate(p)


def test_all_proposition_spans_reproduce_source_text():
    excerpt = ref().source_excerpts[0]
    for p in ref().propositions:
        assert excerpt.content[p.char_start:p.char_end] == p.surface_text
        assert p.proposition_does_not_establish_truth is True


def test_negative_proposition_is_preserved_not_deleted():
    p = {x.proposition_id: x for x in ref().propositions}["proposition:measure-no-emissions-reduction"]
    assert p.surface_text == "the measure did not reduce emissions"
    a = {x.proposition_ref: x for x in ref().assessments}[p.proposition_id]
    assert a.polarity == Polarity.negative
    assert a.negation_scope_ref == "negation-scope:measure-no-emissions-reduction"


def test_negation_scope_is_exact():
    excerpt = ref().source_excerpts[0]
    n = ref().negation_scopes[0]
    assert excerpt.content[n.scope_char_start:n.scope_char_end] == "not reduce emissions"
    assert n.polarity == Polarity.negative
    assert n.negation_scope_is_linguistic_analysis_not_truth_verdict is True


def test_may_is_possible_modality():
    a = {x.proposition_ref: x for x in ref().assessments}["proposition:may-lower-costs"]
    assert a.modal_force == ModalForce.possible
    assert a.certainty_level == CertaintyLevel.low
    assert a.epistemic_state == EpistemicState.attributed
    assert a.modal_scope_ref == "modal-scope:may-lower-costs"


def test_could_in_conditional_is_possible_and_hypothetical():
    a = {x.proposition_ref: x for x in ref().assessments}["proposition:adoption-could-increase"]
    assert a.modal_force == ModalForce.possible
    assert a.epistemic_state == EpistemicState.hypothetical
    assert a.conditional_scope_ref == "conditional-scope:subsidies-extended"


def test_conditional_is_not_asserted_realized():
    c = ref().conditional_scopes[0]
    assert c.condition_text == "If subsidies were extended"
    assert c.condition_is_not_asserted_as_realized is True


def test_explicit_uncertainty_is_not_model_confidence():
    a = {x.proposition_ref: x for x in ref().assessments}["proposition:estimate-uncertain"]
    assert a.epistemic_state == EpistemicState.uncertain
    assert a.certainty_level == CertaintyLevel.explicit_uncertainty
    assert a.linguistic_confidence == 0.99
    assert a.linguistic_confidence_is_not_claim_probability is True


def test_reported_assertion_is_attributed_not_platform_truth():
    a = {x.proposition_ref: x for x in ref().assessments}["proposition:measure-no-emissions-reduction"]
    assert a.epistemic_state == EpistemicState.reported
    assert a.attribution_ref == "attribution:report-states"
    assert a.epistemic_state_is_not_platform_truth_state is True
    assert a.evidence_status_unchanged is True


def test_all_surface_attributions_leave_canonical_identity_unbound():
    for a in ref().attributions:
        assert a.canonical_actor_ref is None
        assert a.surface_source_does_not_establish_canonical_identity is True
        assert a.attribution_does_not_validate_proposition is True


def test_attributions_bind_expected_propositions():
    attrs = {x.attribution_id: x for x in ref().attributions}
    assert attrs["attribution:report-states"].proposition_refs == ["proposition:measure-no-emissions-reduction"]
    assert attrs["attribution:researchers-suggest"].proposition_refs == ["proposition:may-lower-costs"]
    assert attrs["attribution:ministry-says"].proposition_refs == ["proposition:estimate-uncertain"]


def test_cue_spans_reproduce_source():
    excerpt = ref().source_excerpts[0]
    for cue in ref().cues:
        assert excerpt.content[cue.char_start:cue.char_end] == cue.surface_text


def test_cue_types_cover_epistemic_dimensions():
    types = {x.cue_type for x in ref().cues}
    assert {"attribution", "modal", "negation", "certainty", "conditional"}.issubset(types)


def test_v43_it_reference_is_reused_not_rewritten():
    p = {x.proposition_id: x for x in ref().propositions}["proposition:may-lower-costs"]
    assert p.predecessor_reference_ref == "reference-expression:it"
    assert ref().temporal_spatial_grounding.referential_identity.candidate_sets[0].selected_candidate_ref == "candidate:it:proposal"


def test_v44_groundings_are_preserved():
    predecessor = ref().temporal_spatial_grounding
    assert predecessor.release == "4.4.0"
    assert predecessor.spatial_groundings[1].spatial_anchor_ref == "spatial-anchor:brussels-source-place"
    assert predecessor.temporal_groundings[1].temporal_anchor_ref == "temporal-anchor:calendar-year:2026"


def test_policy_keeps_certainty_separate_from_confidence():
    p = ref().policy
    assert p.certainty_is_distinct_from_model_confidence is True
    assert p.epistemic_state_does_not_promote_evidence is True
    assert p.canonical_speaker_identity_is_not_inferred_from_surface_form is True


def test_policy_forbids_graph_mutation():
    p = ref().policy
    assert p.identity_graph_mutation_authorized is False
    assert p.evidence_graph_mutation_authorized is False
    assert p.context_graph_mutation_authorized is False
    assert p.knowledge_graph_mutation_authorized is False


def test_contract_boundaries_are_explicit():
    b = contract_document()["boundaries"]
    assert b["reported_claim_establishes_platform_truth"] is False
    assert b["source_certainty_establishes_evidence_validity"] is False
    assert b["linguistic_confidence_is_claim_probability"] is False
    assert b["modal_possibility_is_prediction_probability"] is False
    assert b["conditional_language_establishes_condition_realized"] is False
    assert b["surface_source_establishes_canonical_actor_identity"] is False
    assert b["accepted_epistemic_analysis_rewrites_v440_predecessor"] is False


def test_contract_graph_boundaries_are_false():
    b = contract_document()["boundaries"]
    assert b["identity_graph_mutation_performed"] is False
    assert b["evidence_graph_mutation_performed"] is False
    assert b["context_graph_mutation_performed"] is False
    assert b["knowledge_graph_mutation_performed"] is False


def test_all_assessments_are_governed_reviewed():
    for a in ref().assessments:
        assert a.state == EpistemicReviewState.accepted
        assert a.reviewer_ref == "reviewer:epistemic-semantics:v1"
        assert a.evidence_status_unchanged is True


def test_negative_assessment_requires_negation_scope():
    p = ref().assessments[0].model_dump(mode="python")
    p["negation_scope_ref"] = None
    with pytest.raises(ValidationError):
        EpistemicAssessment.model_validate(p)


def test_modal_assessment_requires_modal_scope():
    p = ref().assessments[1].model_dump(mode="python")
    p["modal_scope_ref"] = None
    with pytest.raises(ValidationError):
        EpistemicAssessment.model_validate(p)


def test_accepted_assessment_requires_reviewer():
    p = ref().assessments[0].model_dump(mode="python")
    p["reviewer_ref"] = None
    with pytest.raises(ValidationError):
        EpistemicAssessment.model_validate(p)


def test_proposition_span_mismatch_rejected():
    invalid(lambda p: p["propositions"][0].__setitem__("char_start", p["propositions"][0]["char_start"] + 1))


def test_proposition_source_ref_must_resolve():
    invalid(lambda p: p["propositions"][0].__setitem__("source_excerpt_ref", "epistemic-source:missing"))


def test_predecessor_reference_must_resolve():
    invalid(lambda p: p["propositions"][1].__setitem__("predecessor_reference_ref", "reference-expression:missing"))


def test_attribution_proposition_must_resolve():
    invalid(lambda p: p["attributions"][0]["proposition_refs"].append("proposition:missing"))


def test_cue_proposition_must_resolve():
    invalid(lambda p: p["cues"][0].__setitem__("proposition_ref", "proposition:missing"))


def test_cue_span_mismatch_rejected():
    invalid(lambda p: p["cues"][0].__setitem__("char_start", p["cues"][0]["char_start"] + 1))


def test_negation_scope_cue_must_resolve():
    invalid(lambda p: p["negation_scopes"][0].__setitem__("cue_ref", "cue:missing"))


def test_negation_scope_span_mismatch_rejected():
    invalid(lambda p: p["negation_scopes"][0].__setitem__("scope_char_start", p["negation_scopes"][0]["scope_char_start"] + 1))


def test_modal_scope_cue_must_resolve():
    invalid(lambda p: p["modal_scopes"][0].__setitem__("cue_ref", "cue:missing"))


def test_conditional_scope_proposition_must_resolve():
    invalid(lambda p: p["conditional_scopes"][0].__setitem__("consequent_proposition_ref", "proposition:missing"))


def test_conditional_span_mismatch_rejected():
    invalid(lambda p: p["conditional_scopes"][0].__setitem__("condition_char_start", 1))


def test_assessment_attribution_must_resolve():
    invalid(lambda p: p["assessments"][0].__setitem__("attribution_ref", "attribution:missing"))


def test_assessment_negation_must_resolve():
    invalid(lambda p: p["assessments"][0].__setitem__("negation_scope_ref", "negation-scope:missing"))


def test_assessment_modal_must_resolve():
    invalid(lambda p: p["assessments"][1].__setitem__("modal_scope_ref", "modal-scope:missing"))


def test_interpretation_preserves_predecessor_and_truth_boundary():
    i = ref().interpretations[0]
    assert i.predecessor_grounding_interpretation_ref == ref().temporal_spatial_grounding.interpretations[0].interpretation_id
    assert i.predecessor_objects_remain_immutable is True
    assert i.interpretation_is_not_truth_verdict is True
    assert i.interpretation_does_not_change_evidence_status is True


def test_interpretation_assessment_refs_must_resolve():
    invalid(lambda p: p["interpretations"][0]["assessment_refs"].append("assessment:missing"))


def test_snapshot_binds_exact_v44_fingerprint():
    snap = ref().snapshots[0]
    assert snap.predecessor_fingerprint_sha256 == ref().temporal_spatial_grounding.fingerprint()
    assert snap.immutable is True
    assert snap.supersedable is True
    assert snap.snapshot_does_not_freeze_truth is True


def test_snapshot_predecessor_fingerprint_must_match():
    invalid(lambda p: p["snapshots"][0].__setitem__("predecessor_fingerprint_sha256", "0" * 64))


def test_provenance_subject_must_resolve():
    invalid(lambda p: p["provenance_records"][0]["subject_refs"].append("missing:object"))


def test_no_database_migration():
    assert ref().database_migration == "none"
    assert contract_document()["database_migration"] == "none"


def test_schema_roundtrip():
    rebuilt = EpistemicModalNegationCertaintyBundle.model_validate(payload())
    assert rebuilt.fingerprint() == ref().fingerprint()


def test_schema_generation():
    schema = EpistemicModalNegationCertaintyBundle.model_json_schema()
    assert schema["title"] == "EpistemicModalNegationCertaintyBundle"
    assert "$defs" in schema


def test_public_contract_route():
    client = TestClient(create_app())
    r = client.get("/public/v1/epistemic-semantics/contract")
    assert r.status_code == 200
    body = r.json()
    assert body["release"] == "4.5.0"
    assert body["contract"] == CONTRACT_VERSION
    assert body["reference"]["propositions"] == 4


def test_private_reference_route():
    client = TestClient(create_app())
    r = client.get("/v1/epistemic-semantics/reference")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["bundle"]["release"] == "4.5.0"
    assert len(body["bundle_fingerprint_sha256"]) == 64


def test_validation_routes():
    client = TestClient(create_app())
    assert client.post("/v1/epistemic-semantics/validate-proposition", json=ref().propositions[0].model_dump(mode="json")).status_code == 200
    assert client.post("/v1/epistemic-semantics/validate-assessment", json=ref().assessments[0].model_dump(mode="json")).status_code == 200
    assert client.post("/v1/epistemic-semantics/validate-negation-scope", json=ref().negation_scopes[0].model_dump(mode="json")).status_code == 200
    assert client.post("/v1/epistemic-semantics/validate-modal-scope", json=ref().modal_scopes[0].model_dump(mode="json")).status_code == 200


def test_main_app_mounts_v45_routes():
    paths = {route.path for route in create_app().routes}
    assert "/v1/epistemic-semantics/contract" in paths
    assert "/public/v1/epistemic-semantics/contract" in paths
    assert "/v1/epistemic-semantics/reference" in paths


def test_reference_fingerprint_is_deterministic():
    assert ref().fingerprint() == reference_epistemic_modal_negation_certainty_bundle().fingerprint()
