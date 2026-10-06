from copy import deepcopy

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.config import Settings
from app.main import create_app
from app.services.temporal_spatial_language_grounding import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    EXTENDS_CONTRACTS,
    GroundingCandidate,
    GroundingCandidateSet,
    GroundingDomain,
    GroundingPolicy,
    GroundingSourceExcerpt,
    GroundingState,
    SpatialAnchor,
    SpatialAnchorKind,
    SpatialExpression,
    SpatialExpressionKind,
    TemporalAnchor,
    TemporalAnchorKind,
    TemporalExpression,
    TemporalExpressionKind,
    TemporalRelationKind,
    TemporalSpatialLanguageGroundingBundle,
    contract_document,
    reference_temporal_spatial_language_grounding_bundle,
)
from app.services.coreference_referential_identity import CONTRACT_VERSION as V43_CONTRACT


def ref():
    return reference_temporal_spatial_language_grounding_bundle()


def payload():
    return ref().model_dump(mode="python")


def invalid(mutator):
    p = deepcopy(payload())
    mutator(p)
    with pytest.raises(ValidationError):
        TemporalSpatialLanguageGroundingBundle.model_validate(p)


def test_release_identity():
    assert CORE_RELEASE == "4.4.0"
    assert CONTRACT_VERSION == "sc.core.temporal-spatial-language-grounding.v1"
    version = tuple(int(x) for x in Settings().version.split("."))
    assert version >= (4, 4, 0)
    assert ref().release == "4.4.0"


def test_predecessor_is_v43_referential_identity():
    assert ref().predecessor_contract == V43_CONTRACT
    assert ref().referential_identity.release == "4.3.0"
    assert ref().referential_identity.contract == V43_CONTRACT


def test_dependency_order_is_governed():
    assert ref().extends_contracts == EXTENDS_CONTRACTS
    invalid(lambda p: p["extends_contracts"].reverse())


def test_reference_counts():
    c = contract_document()["reference"]
    assert c["source_excerpts"] == 1
    assert c["temporal_expressions"] == 3
    assert c["spatial_expressions"] == 2
    assert c["temporal_anchors"] == 3
    assert c["spatial_anchors"] == 1
    assert c["candidate_sets"] == 5
    assert c["candidates"] == 5
    assert c["accepted_candidate_sets"] == 5
    assert c["temporal_groundings"] == 3
    assert c["spatial_groundings"] == 2
    assert c["temporal_relation_groundings"] == 1
    assert c["unresolved_expressions"] == 0


def test_predecessor_v43_coreference_resolution_is_preserved():
    p = ref().referential_identity
    assert p.candidate_sets[0].selected_candidate_ref == "candidate:it:proposal"
    assert p.coreference_links[0].antecedent_referent_ref == "referent:proposal"
    assert p.discourse_semantics.context_semantics.mentions[-1].surface_text == "It"


def test_reference_source_excerpt_is_immutable_and_hashed():
    s = ref().source_excerpts[0]
    assert s.source_excerpt_is_immutable is True
    assert s.content.startswith("In 2025")
    assert len(s.content_sha256) == 64


def test_absolute_year_expression_span_is_exact():
    e = {x.temporal_expression_id: x for x in ref().temporal_expressions}["temporal-expression:2025"]
    assert e.expression_kind == TemporalExpressionKind.absolute_year
    assert e.surface_text == "2025"
    assert (e.char_start, e.char_end) == (3, 7)


def test_relative_year_preserves_base_expression():
    e = {x.temporal_expression_id: x for x in ref().temporal_expressions}["temporal-expression:following-year"]
    assert e.expression_kind == TemporalExpressionKind.relative_time
    assert e.base_temporal_expression_ref == "temporal-expression:2025"
    assert e.metadata["relative_operation"] == "+P1Y"


def test_named_place_expression_span_is_exact():
    e = {x.spatial_expression_id: x for x in ref().spatial_expressions}["spatial-expression:brussels"]
    assert e.expression_kind == SpatialExpressionKind.named_place
    assert e.surface_text == "Brussels"
    assert (e.char_start, e.char_end) == (42, 50)


def test_spatial_deixis_preserves_antecedent():
    e = {x.spatial_expression_id: x for x in ref().spatial_expressions}["spatial-expression:there"]
    assert e.expression_kind == SpatialExpressionKind.spatial_deixis
    assert e.antecedent_expression_ref == "spatial-expression:brussels"
    assert e.surface_text == "there"


def test_absolute_year_anchor_is_year_interval():
    a = {x.temporal_anchor_id: x for x in ref().temporal_anchors}["temporal-anchor:calendar-year:2025"]
    assert a.anchor_kind == TemporalAnchorKind.calendar_period
    assert a.normalized_start == "2025-01-01"
    assert a.normalized_end == "2025-12-31"
    assert a.precision == "year"


def test_relative_year_anchor_preserves_derivation():
    a = {x.temporal_anchor_id: x for x in ref().temporal_anchors}["temporal-anchor:calendar-year:2026"]
    assert a.anchor_kind == TemporalAnchorKind.derived
    assert a.base_anchor_ref == "temporal-anchor:calendar-year:2025"
    assert a.derivation_operation == "+P1Y"
    assert a.normalized_start == "2026-01-01"


def test_brussels_anchor_does_not_claim_canonical_identity():
    a = ref().spatial_anchors[0]
    assert a.label == "Brussels"
    assert a.canonical_place_ref is None
    assert a.canonical_geographic_identity_established is False
    assert contract_document()["reference"]["canonical_place_bindings"] == 0


def test_there_and_brussels_ground_to_same_source_place_anchor():
    gs = {x.spatial_expression_ref: x for x in ref().spatial_groundings}
    assert gs["spatial-expression:brussels"].spatial_anchor_ref == "spatial-anchor:brussels-source-place"
    assert gs["spatial-expression:there"].spatial_anchor_ref == "spatial-anchor:brussels-source-place"
    assert gs["spatial-expression:there"].confidence == 0.96


def test_after_signal_is_grounded_to_reported_event_order():
    r = ref().temporal_relation_groundings[0]
    assert r.predecessor_signal_ref == "discourse-signal:after"
    assert r.predecessor_rhetorical_relation_ref == "rhetorical-relation:revision-before-rejection"
    assert r.source_event_ref == "frame:revision"
    assert r.target_event_ref == "frame:rejection"
    assert r.relation_kind == TemporalRelationKind.before
    assert r.relation_does_not_establish_real_world_event_order is True


def test_temporal_relation_does_not_mutate_graph():
    b = contract_document()["boundaries"]
    assert b["temporal_relation_establishes_real_world_event_order"] is False
    assert b["temporal_graph_mutation_performed"] is False


def test_spatial_grounding_does_not_geocode_autonomously():
    b = contract_document()["boundaries"]
    assert b["core_autonomously_geocodes_named_place"] is False
    assert b["named_place_establishes_canonical_geographic_identity"] is False
    assert b["spatial_graph_mutation_performed"] is False


def test_policy_preserves_grounding_boundaries():
    p = ref().policy
    assert p.relative_grounding_preserves_base_anchor is True
    assert p.place_name_does_not_establish_canonical_geographic_identity is True
    assert p.temporal_relation_is_source_semantics_not_world_truth is True
    assert p.temporal_graph_mutation_authorized is False
    assert p.spatial_graph_mutation_authorized is False


def test_all_candidate_sets_are_reviewed_and_accepted():
    for s in ref().candidate_sets:
        assert s.state == GroundingState.accepted
        assert s.selected_candidate_ref in s.candidate_refs
        assert s.reviewer_ref == "reviewer:language-grounding:v1"


def test_candidate_domains_match_anchors():
    temporal_anchors = {x.temporal_anchor_id for x in ref().temporal_anchors}
    spatial_anchors = {x.spatial_anchor_id for x in ref().spatial_anchors}
    for c in ref().candidates:
        if c.domain == GroundingDomain.temporal:
            assert c.anchor_ref in temporal_anchors
        else:
            assert c.anchor_ref in spatial_anchors


def test_grounding_interpretation_does_not_rewrite_predecessor():
    i = ref().interpretations[0]
    assert i.interpretation_does_not_rewrite_predecessor_objects is True
    assert i.interpretation_is_not_world_truth_verdict is True
    assert i.unresolved_expression_refs == []


def test_snapshot_binds_exact_v43_fingerprint():
    snap = ref().snapshots[0]
    assert snap.predecessor_fingerprint_sha256 == ref().referential_identity.fingerprint()
    assert snap.immutable is True
    assert snap.supersedable is True


def test_no_database_migration():
    assert ref().database_migration == "none"
    assert contract_document()["database_migration"] == "none"


def test_source_hash_mismatch_rejected():
    p = ref().source_excerpts[0].model_dump(mode="python")
    p["content"] += " changed"
    with pytest.raises(ValidationError):
        GroundingSourceExcerpt.model_validate(p)


def test_temporal_expression_requires_source_locator():
    p = ref().temporal_expressions[0].model_dump(mode="python")
    p["source_excerpt_ref"] = None
    p["predecessor_signal_ref"] = None
    with pytest.raises(ValidationError):
        TemporalExpression.model_validate(p)


def test_temporal_expression_span_must_match_source():
    invalid(lambda p: p["temporal_expressions"][0].__setitem__("char_start", 4))


def test_spatial_expression_span_must_match_source():
    invalid(lambda p: p["spatial_expressions"][0].__setitem__("char_start", 41))


def test_temporal_expression_source_excerpt_must_resolve():
    invalid(lambda p: p["temporal_expressions"][0].__setitem__("source_excerpt_ref", "grounding-source:missing"))


def test_spatial_expression_source_excerpt_must_resolve():
    invalid(lambda p: p["spatial_expressions"][0].__setitem__("source_excerpt_ref", "grounding-source:missing"))


def test_relative_temporal_expression_base_must_resolve():
    invalid(lambda p: p["temporal_expressions"][1].__setitem__("base_temporal_expression_ref", "temporal-expression:missing"))


def test_spatial_deictic_antecedent_must_resolve():
    invalid(lambda p: p["spatial_expressions"][1].__setitem__("antecedent_expression_ref", "spatial-expression:missing"))


def test_derived_temporal_anchor_requires_base_and_operation():
    p = ref().temporal_anchors[1].model_dump(mode="python")
    p["base_anchor_ref"] = None
    with pytest.raises(ValidationError):
        TemporalAnchor.model_validate(p)


def test_event_temporal_anchor_requires_event_ref():
    p = ref().temporal_anchors[2].model_dump(mode="python")
    p["event_ref"] = None
    with pytest.raises(ValidationError):
        TemporalAnchor.model_validate(p)


def test_temporal_anchor_base_must_resolve():
    invalid(lambda p: p["temporal_anchors"][1].__setitem__("base_anchor_ref", "temporal-anchor:missing"))


def test_temporal_anchor_event_ref_must_resolve():
    invalid(lambda p: p["temporal_anchors"][2].__setitem__("event_ref", "frame:missing"))


def test_canonical_place_anchor_requires_canonical_ref():
    p = ref().spatial_anchors[0].model_dump(mode="python")
    p["anchor_kind"] = SpatialAnchorKind.canonical_place
    with pytest.raises(ValidationError):
        SpatialAnchor.model_validate(p)


def test_candidate_set_expression_must_resolve():
    invalid(lambda p: p["candidate_sets"][0].__setitem__("expression_ref", "temporal-expression:missing"))


def test_candidate_set_domain_must_match_expression():
    invalid(lambda p: p["candidate_sets"][0].__setitem__("domain", "spatial"))


def test_candidate_anchor_must_resolve():
    invalid(lambda p: p["candidates"][0].__setitem__("anchor_ref", "temporal-anchor:missing"))


def test_candidate_domain_must_match_anchor():
    invalid(lambda p: p["candidates"][0].__setitem__("domain", "spatial"))


def test_candidate_ranks_must_be_unique_within_set():
    p = payload()
    clone = deepcopy(p["candidates"][0])
    clone["candidate_id"] = "grounding-candidate:2025:duplicate"
    clone["rank"] = 1
    p["candidates"].append(clone)
    p["candidate_sets"][0]["candidate_refs"].append(clone["candidate_id"])
    with pytest.raises(ValidationError):
        TemporalSpatialLanguageGroundingBundle.model_validate(p)


def test_accepted_candidate_set_requires_reviewer():
    p = ref().candidate_sets[0].model_dump(mode="python")
    p["reviewer_ref"] = None
    with pytest.raises(ValidationError):
        GroundingCandidateSet.model_validate(p)


def test_unresolved_candidate_set_cannot_select():
    p = ref().candidate_sets[0].model_dump(mode="python")
    p["state"] = GroundingState.unresolved
    with pytest.raises(ValidationError):
        GroundingCandidateSet.model_validate(p)


def test_temporal_grounding_must_agree_with_selected_candidate():
    invalid(lambda p: p["temporal_groundings"][0].__setitem__("temporal_anchor_ref", "temporal-anchor:calendar-year:2026"))


def test_spatial_grounding_must_agree_with_selected_candidate():
    invalid(lambda p: p["spatial_groundings"][0].__setitem__("selected_candidate_ref", "grounding-candidate:there:brussels"))


def test_accepted_grounding_requires_accepted_candidate():
    invalid(lambda p: p["candidates"][0].__setitem__("state", "reviewed"))


def test_temporal_relation_rhetorical_relation_must_resolve():
    invalid(lambda p: p["temporal_relation_groundings"][0].__setitem__("predecessor_rhetorical_relation_ref", "rhetorical-relation:missing"))


def test_temporal_relation_signal_must_resolve():
    invalid(lambda p: p["temporal_relation_groundings"][0].__setitem__("predecessor_signal_ref", "discourse-signal:missing"))


def test_temporal_relation_event_refs_must_resolve():
    invalid(lambda p: p["temporal_relation_groundings"][0].__setitem__("source_event_ref", "frame:missing"))


def test_interpretation_predecessor_interpretation_must_resolve():
    invalid(lambda p: p["interpretations"][0].__setitem__("referential_interpretation_ref", "referential-interpretation:missing"))


def test_snapshot_predecessor_fingerprint_must_match():
    invalid(lambda p: p["snapshots"][0].__setitem__("predecessor_fingerprint_sha256", "0" * 64))


def test_contract_boundaries_are_explicit():
    b = contract_document()["boundaries"]
    assert b["core_autonomously_selects_grounding"] is False
    assert b["grounding_score_establishes_world_truth"] is False
    assert b["relative_time_flattens_derivation_history"] is False
    assert b["accepted_grounding_rewrites_v430_predecessor"] is False
    assert b["identity_graph_mutation_performed"] is False
    assert b["evidence_graph_mutation_performed"] is False
    assert b["context_graph_mutation_performed"] is False


def test_schema_roundtrip():
    assert TemporalSpatialLanguageGroundingBundle.model_validate(payload()).fingerprint() == ref().fingerprint()


def test_public_contract_route():
    client = TestClient(create_app())
    r = client.get("/public/v1/language-grounding/contract")
    assert r.status_code == 200
    body = r.json()
    assert body["release"] == "4.4.0"
    assert body["contract"] == CONTRACT_VERSION
    assert body["reference"]["temporal_expressions"] == 3
    assert body["reference"]["spatial_expressions"] == 2


def test_private_reference_route():
    client = TestClient(create_app())
    r = client.get("/v1/language-grounding/reference")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["bundle"]["release"] == "4.4.0"
    assert len(body["bundle_fingerprint_sha256"]) == 64


def test_validation_routes():
    client = TestClient(create_app())
    temporal = ref().temporal_expressions[0].model_dump(mode="json")
    spatial = ref().spatial_expressions[0].model_dump(mode="json")
    assert client.post("/v1/language-grounding/validate-temporal-expression", json=temporal).status_code == 200
    assert client.post("/v1/language-grounding/validate-spatial-expression", json=spatial).status_code == 200


def test_main_app_mounts_v44_routes():
    paths = {route.path for route in create_app().routes}
    assert "/v1/language-grounding/contract" in paths
    assert "/public/v1/language-grounding/contract" in paths
    assert "/v1/language-grounding/reference" in paths


def test_reference_fingerprint_is_deterministic():
    assert ref().fingerprint() == reference_temporal_spatial_language_grounding_bundle().fingerprint()
