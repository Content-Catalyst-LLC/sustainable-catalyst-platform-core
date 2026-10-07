from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.config import Settings
from app.main import create_app
from app.routers import pragmatic_meaning_speech_act_intent as api
from app.services.epistemic_modal_negation_certainty import CONTRACT_VERSION as V45_CONTRACT
from app.services.pragmatic_meaning_speech_act_intent import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    EXTENDS_CONTRACTS,
    CommunicativeIntent,
    CommunicativeIntentType,
    GenreType,
    PragmaticContext,
    PragmaticMeaningSpeechActIntentBundle,
    PragmaticReviewState,
    PragmaticSourceExcerpt,
    RegisterType,
    SpeechAct,
    SpeechActType,
    contract_document,
    reference_pragmatic_meaning_speech_act_intent_bundle,
)


def ref():
    return reference_pragmatic_meaning_speech_act_intent_bundle()


def payload():
    return ref().model_dump(mode="python")


def invalid(mutator):
    p = deepcopy(payload())
    mutator(p)
    with pytest.raises(ValidationError):
        PragmaticMeaningSpeechActIntentBundle.model_validate(p)


def test_release_identity():
    assert CORE_RELEASE == "4.6.0"
    assert CONTRACT_VERSION == "sc.core.pragmatic-meaning-speech-act-communicative-intent.v1"
    assert tuple(map(int, Settings().version.split("."))) >= (4, 6, 0)
    assert ref().release == "4.6.0"


def test_predecessor_is_v45_epistemic_semantics():
    assert ref().predecessor_contract == V45_CONTRACT
    assert ref().epistemic_semantics.release == "4.5.0"
    assert ref().epistemic_semantics.contract == V45_CONTRACT


def test_dependency_order_is_governed():
    assert ref().extends_contracts == EXTENDS_CONTRACTS
    invalid(lambda p: p["extends_contracts"].reverse())


def test_reference_counts():
    c = contract_document()["reference"]
    assert c["source_excerpts"] == 1
    assert c["participants"] == 2
    assert c["content_units"] == 5
    assert c["cues"] == 6
    assert c["contexts"] == 1
    assert c["speech_acts"] == 5
    assert c["intents"] == 5
    assert c["assertions"] == 1
    assert c["requests"] == 1
    assert c["recommendations"] == 1
    assert c["warnings"] == 1
    assert c["commitments"] == 1
    assert c["canonical_actor_bindings"] == 0


def test_intent_counts():
    c = contract_document()["reference"]
    assert c["inform_intents"] == 1
    assert c["elicit_action_intents"] == 1
    assert c["advise_intents"] == 1
    assert c["alert_intents"] == 1
    assert c["commit_intents"] == 1


def test_source_excerpt_is_immutable_and_hashed():
    s = ref().source_excerpts[0]
    assert s.immutable is True
    assert s.source_excerpt_is_not_truth_validation is True
    assert s.content.startswith("At the public hearing")
    assert len(s.content_sha256) == 64


def test_source_hash_mismatch_rejected():
    p = ref().source_excerpts[0].model_dump(mode="python")
    p["content"] += " altered"
    with pytest.raises(ValidationError):
        PragmaticSourceExcerpt.model_validate(p)


def test_content_unit_spans_reproduce_source_text():
    excerpt = ref().source_excerpts[0]
    for unit in ref().content_units:
        assert excerpt.content[unit.char_start:unit.char_end] == unit.surface_text
        assert unit.content_unit_does_not_establish_truth is True


def test_pragmatic_cue_spans_reproduce_source_text():
    excerpt = ref().source_excerpts[0]
    for cue in ref().cues:
        assert excerpt.content[cue.char_start:cue.char_end] == cue.surface_text
        assert cue.cue_is_interpretive_evidence_not_world_fact is True


def test_surface_participants_are_preserved_without_canonical_identity():
    assert {p.participant_id for p in ref().participants} == {
        "participant:agency-speaker",
        "participant:residents-audience",
    }
    assert all(p.canonical_actor_ref is None for p in ref().participants)
    assert all(p.surface_form_does_not_establish_canonical_identity is True for p in ref().participants)


def test_reference_context_is_public_hearing_formal_register():
    c = ref().contexts[0]
    assert c.genre == GenreType.public_hearing
    assert c.register_type == RegisterType.formal
    assert c.setting_text == "public hearing"
    assert c.state == PragmaticReviewState.accepted
    assert c.reviewer_ref == "reviewer:pragmatic-semantics:v1"


def test_reference_speech_act_types():
    acts = {a.speech_act_id: a.act_type for a in ref().speech_acts}
    assert acts["speech-act:assert-measure"] == SpeechActType.assertion
    assert acts["speech-act:request-comments"] == SpeechActType.request
    assert acts["speech-act:recommend-delay"] == SpeechActType.recommendation
    assert acts["speech-act:warn-disruption"] == SpeechActType.warning
    assert acts["speech-act:commit-revised-plan"] == SpeechActType.commitment


def test_reference_communicative_intents():
    intents = {i.intent_id: i.intent_type for i in ref().intents}
    assert intents["intent:inform-measure"] == CommunicativeIntentType.inform
    assert intents["intent:elicit-comments"] == CommunicativeIntentType.elicit_action
    assert intents["intent:advise-delay"] == CommunicativeIntentType.advise
    assert intents["intent:alert-disruption"] == CommunicativeIntentType.alert
    assert intents["intent:commit-plan"] == CommunicativeIntentType.commit


def test_policy_preserves_pragmatic_epistemic_boundaries():
    p = ref().policy
    assert p.speech_act_is_distinct_from_proposition_truth is True
    assert p.communicative_intent_is_distinct_from_outcome is True
    assert p.communicative_intent_does_not_claim_private_mental_state is True
    assert p.genre_and_register_are_interpretations_not_authority_scores is True
    assert p.predecessor_epistemic_objects_remain_immutable is True


def test_policy_specific_act_boundaries():
    p = ref().policy
    assert p.request_does_not_create_platform_obligation is True
    assert p.recommendation_does_not_establish_normative_correctness is True
    assert p.warning_does_not_establish_risk_as_fact is True
    assert p.commitment_does_not_guarantee_future_performance is True


def test_policy_forbids_graph_mutation():
    p = ref().policy
    assert p.identity_graph_mutation_authorized is False
    assert p.evidence_graph_mutation_authorized is False
    assert p.context_graph_mutation_authorized is False
    assert p.knowledge_graph_mutation_authorized is False


def test_contract_boundaries_are_explicit():
    b = contract_document()["boundaries"]
    assert b["assertion_establishes_platform_truth"] is False
    assert b["request_creates_platform_obligation"] is False
    assert b["recommendation_establishes_normative_correctness"] is False
    assert b["warning_establishes_risk_as_fact"] is False
    assert b["commitment_guarantees_future_performance"] is False
    assert b["communicative_intent_reveals_private_mental_state"] is False
    assert b["genre_or_register_establishes_source_authority"] is False
    assert b["surface_speaker_establishes_canonical_actor_identity"] is False
    assert b["accepted_pragmatic_analysis_rewrites_v450_predecessor"] is False


def test_contract_graph_boundaries_are_false():
    b = contract_document()["boundaries"]
    assert b["identity_graph_mutation_performed"] is False
    assert b["evidence_graph_mutation_performed"] is False
    assert b["context_graph_mutation_performed"] is False
    assert b["knowledge_graph_mutation_performed"] is False


def test_all_accepted_speech_acts_are_reviewed():
    for a in ref().speech_acts:
        assert a.state == PragmaticReviewState.accepted
        assert a.reviewer_ref == "reviewer:pragmatic-semantics:v1"
        assert a.act_classification_is_not_truth_verdict is True
        assert a.act_classification_does_not_create_legal_or_normative_force is True


def test_all_accepted_intents_are_reviewed():
    for i in ref().intents:
        assert i.state == PragmaticReviewState.accepted
        assert i.reviewer_ref == "reviewer:pragmatic-semantics:v1"
        assert i.intent_is_interpretation_not_private_mental_state is True
        assert i.intent_does_not_establish_communicative_success is True


def test_accepted_context_requires_reviewer():
    p = ref().contexts[0].model_dump(mode="python")
    p["reviewer_ref"] = None
    with pytest.raises(ValidationError):
        PragmaticContext.model_validate(p)


def test_accepted_speech_act_requires_reviewer():
    p = ref().speech_acts[0].model_dump(mode="python")
    p["reviewer_ref"] = None
    with pytest.raises(ValidationError):
        SpeechAct.model_validate(p)


def test_accepted_intent_requires_reviewer():
    p = ref().intents[0].model_dump(mode="python")
    p["reviewer_ref"] = None
    with pytest.raises(ValidationError):
        CommunicativeIntent.model_validate(p)


def test_content_unit_span_mismatch_rejected():
    invalid(lambda p: p["content_units"][0].__setitem__("char_start", p["content_units"][0]["char_start"] + 1))


def test_content_unit_source_ref_must_resolve():
    invalid(lambda p: p["content_units"][0].__setitem__("source_excerpt_ref", "pragmatic-source:missing"))


def test_participant_source_ref_must_resolve():
    invalid(lambda p: p["participants"][0].__setitem__("source_excerpt_ref", "pragmatic-source:missing"))


def test_participant_surface_form_must_appear_in_source():
    invalid(lambda p: p["participants"][0]["surface_forms"].append("not in source"))


def test_cue_span_mismatch_rejected():
    invalid(lambda p: p["cues"][0].__setitem__("char_start", p["cues"][0]["char_start"] + 1))


def test_cue_content_unit_ref_must_resolve():
    invalid(lambda p: p["cues"][1].__setitem__("content_unit_ref", "content:missing"))


def test_context_speaker_ref_must_resolve():
    invalid(lambda p: p["contexts"][0]["speaker_refs"].append("participant:missing"))


def test_context_audience_ref_must_resolve():
    invalid(lambda p: p["contexts"][0]["audience_refs"].append("participant:missing"))


def test_context_cue_ref_must_resolve():
    invalid(lambda p: p["contexts"][0]["cue_refs"].append("cue:missing"))


def test_speech_act_context_ref_must_resolve():
    invalid(lambda p: p["speech_acts"][0].__setitem__("context_ref", "context:missing"))


def test_speech_act_content_ref_must_resolve():
    invalid(lambda p: p["speech_acts"][0].__setitem__("content_unit_ref", "content:missing"))


def test_speech_act_cue_ref_must_resolve():
    invalid(lambda p: p["speech_acts"][0].__setitem__("cue_ref", "cue:missing"))


def test_speech_act_speaker_ref_must_resolve():
    invalid(lambda p: p["speech_acts"][0].__setitem__("speaker_ref", "participant:missing"))


def test_speech_act_audience_ref_must_resolve():
    invalid(lambda p: p["speech_acts"][1]["audience_refs"].append("participant:missing"))


def test_intent_speech_act_ref_must_resolve():
    invalid(lambda p: p["intents"][0].__setitem__("speech_act_ref", "speech-act:missing"))


def test_interpretation_predecessor_ref_must_resolve():
    invalid(lambda p: p["interpretations"][0].__setitem__("predecessor_epistemic_interpretation_ref", "epistemic-interpretation:missing"))


def test_interpretation_context_ref_must_resolve():
    invalid(lambda p: p["interpretations"][0]["context_refs"].append("context:missing"))


def test_interpretation_speech_act_ref_must_resolve():
    invalid(lambda p: p["interpretations"][0]["speech_act_refs"].append("speech-act:missing"))


def test_interpretation_intent_ref_must_resolve():
    invalid(lambda p: p["interpretations"][0]["intent_refs"].append("intent:missing"))


def test_interpretation_preserves_predecessor_and_private_intent_boundary():
    i = ref().interpretations[0]
    assert i.predecessor_epistemic_interpretation_ref == ref().epistemic_semantics.interpretations[0].interpretation_id
    assert i.predecessor_objects_remain_immutable is True
    assert i.interpretation_is_not_truth_verdict is True
    assert i.interpretation_does_not_establish_speaker_private_intent is True
    assert "canonical-actor:agency" in i.unresolved_refs


def test_snapshot_binds_exact_v45_predecessor():
    s = ref().snapshots[0]
    assert s.predecessor_fingerprint_sha256 == ref().epistemic_semantics.fingerprint()
    assert s.immutable is True
    assert s.supersedable is True
    assert s.snapshot_does_not_freeze_truth_or_intent is True


def test_snapshot_predecessor_mismatch_rejected():
    invalid(lambda p: p["snapshots"][0].__setitem__("predecessor_fingerprint_sha256", "0" * 64))


def test_snapshot_interpretation_ref_must_resolve():
    invalid(lambda p: p["snapshots"][0]["interpretation_refs"].append("pragmatic-interpretation:missing"))


def test_provenance_subject_ref_must_resolve():
    invalid(lambda p: p["provenance_records"][0]["subject_refs"].append("object:missing"))


def test_duplicate_speech_act_ids_rejected():
    invalid(lambda p: p["speech_acts"].__setitem__(1, deepcopy(p["speech_acts"][0])))


def test_bundle_fingerprint_is_deterministic():
    assert ref().fingerprint() == reference_pragmatic_meaning_speech_act_intent_bundle().fingerprint()
    assert len(ref().fingerprint()) == 64


def test_contract_document_reference_fingerprint_matches_bundle():
    assert contract_document()["reference"]["bundle_fingerprint_sha256"] == ref().fingerprint()


def test_contract_roadmap_handoff():
    r = contract_document()["roadmap_integration"]
    assert r["extends_v450_epistemic_modal_negation_certainty"] is True
    assert r["prepares_v470_cross_document_context_graph"] is True
    assert r["prepares_v480_multilingual_context_alignment"] is True
    assert r["prepares_v490_contextual_semantic_evaluation"] is True
    assert r["prepares_v4100_unified_contextual_intelligence_runtime"] is True


def test_public_contract_route_function():
    body = api.public_contract()
    assert body["release"] == "4.6.0"
    assert body["contract"] == CONTRACT_VERSION


def test_private_contract_route_function():
    body = api.private_contract()
    assert body["release"] == "4.6.0"


def test_reference_route_function():
    body = api.reference()
    assert body["bundle"]["release"] == "4.6.0"
    assert body["bundle_fingerprint_sha256"] == ref().fingerprint()


def test_validate_context_route_function():
    body = api.validate_context(ref().contexts[0])
    assert body["ok"] is True


def test_validate_speech_act_route_function():
    body = api.validate_speech_act(ref().speech_acts[0])
    assert body["ok"] is True


def test_validate_intent_route_function():
    body = api.validate_intent(ref().intents[0])
    assert body["ok"] is True


def test_validate_bundle_route_function():
    body = api.validate_bundle(ref())
    assert body["fingerprint_sha256"] == ref().fingerprint()


def test_main_app_mounts_v46_routes():
    paths = {route.path for route in create_app().routes}
    assert "/v1/pragmatic-semantics/contract" in paths
    assert "/public/v1/pragmatic-semantics/contract" in paths
    assert "/v1/pragmatic-semantics/validate-bundle" in paths
