from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.config import Settings
from app.routers import claim_alignment_agreement_contradiction as api
from app.services.claim_alignment_agreement_contradiction import (
    AlignmentDimension,
    ClaimAlignmentAgreementContradictionBundle,
    ClaimModality,
    ClaimPolarity,
    ClaimRelationKind,
    ClaimReviewState,
    contract_document,
    reference_claim_alignment_agreement_contradiction_bundle,
)


def ref():
    return reference_claim_alignment_agreement_contradiction_bundle()


def payload():
    return ref().model_dump(mode="json")


def invalid(mutator):
    p = deepcopy(payload())
    mutator(p)
    with pytest.raises((ValidationError, ValueError)):
        ClaimAlignmentAgreementContradictionBundle.model_validate(p)


def test_release_identity():
    assert tuple(int(x) for x in Settings().version.split(".")) >= (4, 13, 0)
    assert ref().release == "4.13.0"
    assert ref().contract == "sc.core.claim-alignment-agreement-contradiction-intelligence.v1"
    assert ref().predecessor_contract == "sc.core.context-retrieval-relevance-intelligence.v1"


def test_v412_predecessor_is_exact_and_preserved():
    assert ref().predecessor_retrieval.release == "4.12.0"
    assert ref().predecessor_retrieval.contract == ref().predecessor_contract
    assert ref().snapshots[0].predecessor_retrieval_fingerprint_sha256 == ref().predecessor_retrieval.fingerprint()


def test_reference_inventory():
    assert len(ref().source_contexts) == 6
    assert len(ref().claims) == 7
    assert len(ref().queries) == 1
    assert len(ref().pairs) == 6
    assert len(ref().signals) == 54
    assert len(ref().assessments) == 6
    assert len(ref().snapshots) == 1


def test_query_requires_all_alignment_dimensions():
    assert set(ref().queries[0].required_dimensions) == set(AlignmentDimension)


def test_every_pair_has_nine_alignment_signals():
    by_pair = {}
    for signal in ref().signals:
        by_pair.setdefault(signal.pair_ref, []).append(signal)
    assert all(len(by_pair[p.pair_id]) == 9 for p in ref().pairs)
    assert all({x.dimension for x in by_pair[p.pair_id]} == set(AlignmentDimension) for p in ref().pairs)


def test_pair_alignment_score_is_signal_mean():
    signals = {x.signal_id: x for x in ref().signals}
    for pair in ref().pairs:
        expected = sum(signals[x].score for x in pair.signal_refs) / len(pair.signal_refs)
        assert pair.alignment_score == pytest.approx(expected)


def test_strict_contradiction_exists_once():
    xs = [x for x in ref().assessments if x.relation_kind == ClaimRelationKind.contradiction]
    assert len(xs) == 1
    pair = next(x for x in ref().pairs if x.pair_id == xs[0].pair_ref)
    assert pair.polarity_conflict is True
    assert pair.modality_mismatch is False
    assert pair.scope_compatible is True


def test_apparent_contradiction_requires_conflict_but_not_strict_scope_alignment():
    xs = [x for x in ref().assessments if x.relation_kind == ClaimRelationKind.apparent_contradiction]
    assert len(xs) == 1
    pair = next(x for x in ref().pairs if x.pair_id == xs[0].pair_ref)
    assert pair.polarity_conflict is True
    assert pair.modality_mismatch is True
    assert pair.scope_compatible is False


def test_qualified_agreements_exist_twice():
    assert sum(x.relation_kind == ClaimRelationKind.qualified_agreement for x in ref().assessments) == 2


def test_partial_agreement_preserves_modal_difference():
    a = next(x for x in ref().assessments if x.relation_kind == ClaimRelationKind.partial_agreement)
    p = next(x for x in ref().pairs if x.pair_id == a.pair_ref)
    assert p.polarity_conflict is False
    assert p.modality_mismatch is True
    assert p.scope_compatible is False


def test_cross_language_agreement_is_contextual():
    a = next(x for x in ref().assessments if x.relation_kind == ClaimRelationKind.agreement)
    p = next(x for x in ref().pairs if x.pair_id == a.pair_ref)
    claims = {x.claim_id: x for x in ref().claims}
    assert {claims[p.left_claim_ref].language_tag, claims[p.right_claim_ref].language_tag} == {"zh", "en"}
    assert "same-policy-object:v48-v47" in p.unresolved_refs


def test_claims_preserve_surface_and_normalization_boundary():
    assert all(x.normalized_for_comparison_only for x in ref().claims)
    assert all(x.normalization_does_not_establish_identity_or_equivalence for x in ref().claims)
    assert all(x.surface_text for x in ref().claims)


def test_negative_report_claim_preserves_polarity_and_asserted_modality():
    c = next(x for x in ref().claims if x.claim_id == "claim:v45:measure-no-emissions-reduction")
    assert c.polarity == ClaimPolarity.negative
    assert c.modality == ClaimModality.asserted
    assert c.source_object_ref == "proposition:measure-no-emissions-reduction"


def test_agency_claim_preserves_possibility_modality():
    c = next(x for x in ref().claims if x.claim_id == "claim:v46:measure-may-reduce-emissions")
    assert c.polarity == ClaimPolarity.positive
    assert c.modality == ClaimModality.possible


def test_direct_emissions_claim_is_narrower_scope():
    c = next(x for x in ref().claims if x.claim_id == "claim:v413:review-no-direct-emissions-reduction")
    assert c.object_scope_key == "emissions:direct-only"
    assert "direct-vs-total-emissions-scope" in c.unresolved_refs


def test_all_pairs_are_reviewed_with_reviewer():
    assert all(x.state == ClaimReviewState.reviewed for x in ref().pairs)
    assert all(x.reviewer_ref == "reviewer:claim-comparison-reference" for x in ref().pairs)


def test_all_assessments_are_reviewed_with_reviewer():
    assert all(x.state == ClaimReviewState.reviewed for x in ref().assessments)
    assert all(x.reviewer_ref == "reviewer:claim-comparison-reference" for x in ref().assessments)


def test_all_pairs_preserve_unresolved_context():
    assert all(x.unresolved_refs for x in ref().pairs)


def test_policy_requires_scope_and_stance_preservation():
    p = ref().policy
    assert p.comparison_requires_explicit_scope is True
    assert p.polarity_difference_alone_is_not_contradiction is True
    assert p.modality_mismatch_may_downgrade_contradiction is True
    assert p.temporal_and_spatial_scope_must_be_compared is True
    assert p.attribution_and_source_stance_must_be_preserved is True


def test_policy_preserves_multilingual_lineage_and_unresolved_identity():
    p = ref().policy
    assert p.multilingual_alignment_must_preserve_translation_lineage is True
    assert p.unresolved_identity_must_not_be_silently_collapsed is True


def test_policy_relation_is_not_truth_or_evidence():
    p = ref().policy
    assert p.reviewed_relation_establishes_truth is False
    assert p.contradiction_identifies_false_claim is False
    assert p.agreement_establishes_evidence_validity is False
    assert p.agreement_count_increases_truth is False
    assert p.source_majority_establishes_truth is False


def test_policy_scores_are_not_credibility_or_deception_scores():
    p = ref().policy
    assert p.alignment_score_is_credibility_score is False
    assert p.contradiction_score_is_deception_score is False


def test_policy_does_not_authorize_graph_mutation():
    p = ref().policy
    assert p.claim_comparison_mutates_predecessor_objects is False
    assert p.context_graph_mutation_authorized is False
    assert p.identity_graph_mutation_authorized is False
    assert p.evidence_graph_mutation_authorized is False
    assert p.knowledge_graph_mutation_authorized is False


def test_provenance_is_bound_to_v412_fingerprint():
    p = ref().provenance_records[0]
    assert p.predecessor_retrieval_fingerprint_sha256 == ref().predecessor_retrieval.fingerprint()
    assert p.replayable is True


def test_snapshot_is_deterministic():
    a = ref().snapshots[0].deterministic_comparison_fingerprint_sha256
    b = reference_claim_alignment_agreement_contradiction_bundle().snapshots[0].deterministic_comparison_fingerprint_sha256
    assert a == b


def test_bundle_fingerprint_is_deterministic():
    assert ref().fingerprint() == reference_claim_alignment_agreement_contradiction_bundle().fingerprint()


def test_contract_reference_counts():
    r = contract_document()["reference"]
    assert r["predecessor_release"] == "4.12.0"
    assert r["source_contexts"] == 6
    assert r["claims"] == 7
    assert r["comparison_pairs"] == 6
    assert r["alignment_signals"] == 54
    assert r["assessments"] == 6
    assert r["strict_contradictions"] == 1
    assert r["apparent_contradictions"] == 1
    assert r["agreements"] == 1
    assert r["qualified_agreements"] == 2
    assert r["partial_agreements"] == 1
    assert r["pairs_with_unresolved_context"] == 6


def test_contract_boundaries_are_explicit():
    b = contract_document()["boundaries"]
    assert b["reviewed_relation_establishes_truth"] is False
    assert b["contradiction_identifies_false_claim"] is False
    assert b["agreement_establishes_evidence_validity"] is False
    assert b["source_majority_establishes_truth"] is False
    assert b["identity_graph_mutation_performed"] is False
    assert b["evidence_graph_mutation_performed"] is False


def test_contract_prepares_reasoning_line():
    r = contract_document()["roadmap_integration"]
    assert r["extends_v4120_context_retrieval_relevance"] is True
    assert r["prepares_v4140_evidence_context_integration"] is True
    assert r["prepares_v4200_unified_contextual_reasoning_runtime"] is True


def test_api_functions_are_directly_callable():
    assert api.contract()["release"] == "4.13.0"
    assert api.public_contract()["contract"] == "sc.core.claim-alignment-agreement-contradiction-intelligence.v1"
    assert api.reference_claims()["count"] == 7
    assert api.reference_pairs()["count"] == 6
    assert api.reference_assessments()["count"] == 6


def test_bad_claim_source_context_fails():
    invalid(lambda p: p["claims"][0].__setitem__("source_context_ref", "claim-source:missing"))


def test_bad_claim_qualification_fails():
    invalid(lambda p: p["claims"][0]["qualification_refs"].__setitem__(0, "qualification:missing"))


def test_bad_query_result_set_fails():
    invalid(lambda p: p["queries"][0].__setitem__("predecessor_result_set_ref", "retrieval-result-set:missing"))


def test_bad_query_claim_ref_fails():
    invalid(lambda p: p["queries"][0]["claim_refs"].__setitem__(0, "claim:missing"))


def test_bad_signal_pair_fails():
    invalid(lambda p: p["signals"][0].__setitem__("pair_ref", "claim-pair:missing"))


def test_bad_pair_claim_ref_fails():
    invalid(lambda p: p["pairs"][0].__setitem__("left_claim_ref", "claim:missing"))


def test_bad_pair_alignment_score_fails():
    invalid(lambda p: p["pairs"][0].__setitem__("alignment_score", 0.123))


def test_bad_pair_polarity_conflict_fails():
    invalid(lambda p: p["pairs"][0].__setitem__("polarity_conflict", False))


def test_bad_pair_modality_mismatch_fails():
    invalid(lambda p: p["pairs"][0].__setitem__("modality_mismatch", False))


def test_strict_contradiction_cannot_ignore_modal_mismatch():
    idx = next(i for i, x in enumerate(payload()["assessments"]) if x["relation_kind"] == "contradiction")
    pair_ref = payload()["assessments"][idx]["pair_ref"]
    pidx = next(i for i, x in enumerate(payload()["pairs"]) if x["pair_id"] == pair_ref)
    invalid(lambda p: p["pairs"][pidx].__setitem__("modality_mismatch", True))


def test_agreement_cannot_have_polarity_conflict():
    idx = next(i for i, x in enumerate(payload()["assessments"]) if x["relation_kind"] == "agreement")
    pair_ref = payload()["assessments"][idx]["pair_ref"]
    pidx = next(i for i, x in enumerate(payload()["pairs"]) if x["pair_id"] == pair_ref)
    # mutate both a claim polarity and the pair flag so pair consistency passes, then agreement rule must fail
    left = payload()["pairs"][pidx]["left_claim_ref"]
    cidx = next(i for i, x in enumerate(payload()["claims"]) if x["claim_id"] == left)
    def mutate(p):
        p["claims"][cidx]["polarity"] = "negative"
        p["pairs"][pidx]["polarity_conflict"] = True
    invalid(mutate)


def test_bad_snapshot_predecessor_fingerprint_fails():
    invalid(lambda p: p["snapshots"][0].__setitem__("predecessor_retrieval_fingerprint_sha256", "0" * 64))


def test_bad_snapshot_claim_fingerprint_fails():
    key = next(iter(payload()["snapshots"][0]["claim_fingerprints"]))
    invalid(lambda p: p["snapshots"][0]["claim_fingerprints"].__setitem__(key, "0" * 64))


def test_database_migration_is_none():
    assert ref().database_migration == "none"
    assert contract_document()["database_migration"] == "none"


def test_main_mounts_v413_routes():
    from app.main import create_app
    app = create_app()
    paths = {r.path for r in app.routes}
    assert "/v1/claim-comparison/contract" in paths
    assert "/public/v1/claim-comparison/contract" in paths
