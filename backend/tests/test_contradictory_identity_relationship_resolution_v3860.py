import copy
import pytest
from pydantic import ValidationError

from app.services.contradictory_identity_relationship_resolution import (
    CONTRACT_VERSION,
    AssertionPosition,
    ContradictionDomain,
    ContradictionResolutionDecision,
    ContradictionResolutionPolicy,
    ContradictionSet,
    ContradictoryAssertionRecord,
    HandoffTarget,
    ResolutionState,
    contract_document,
    reference_contradictory_identity_relationship_resolution_bundle,
)


def ref():
    return reference_contradictory_identity_relationship_resolution_bundle()


def test_contract_identity():
    c = contract_document()
    assert c["release"] == "3.86.0"
    assert c["contract"] == CONTRACT_VERSION
    assert c["database_migration"] == "none"


def test_reference_counts():
    b = ref()
    assert len(b.assertions) == 4
    assert len(b.contradiction_sets) == 2
    assert len(b.criterion_assessments) == 4
    assert len(b.reviews) == 4
    assert len(b.decisions) == 2
    assert len(b.supersessions) == 1
    assert len(b.handoffs) == 2
    assert len(b.snapshots) == 1


@pytest.mark.parametrize("field", [
    "contradiction_is_not_falsity_verdict",
    "majority_agreement_is_not_truth",
    "source_count_is_not_truth",
    "recency_is_not_truth",
    "model_confidence_is_not_truth",
    "resolution_preserves_disfavored_assertion_lineage",
    "unresolved_does_not_imply_equal_evidentiary_support",
])
def test_bundle_principles_true(field):
    assert getattr(ref(), field) is True


@pytest.mark.parametrize("field", [
    "identity_graph_mutation_performed",
    "relationship_graph_mutation_performed",
    "evidence_graph_mutation_performed",
])
def test_bundle_mutations_false(field):
    assert getattr(ref(), field) is False


@pytest.mark.parametrize("field", [
    "contradiction_is_not_falsity_verdict",
    "majority_agreement_is_not_truth",
    "source_count_is_not_truth",
    "recency_is_not_truth",
    "model_confidence_is_not_truth",
    "resolution_preserves_disfavored_assertion_lineage",
    "unresolved_does_not_imply_equal_evidentiary_support",
    "resolution_is_scope_and_provenance_aware",
    "source_disagreement_remains_auditable",
])
def test_contract_principles(field):
    assert contract_document()["principles"][field] is True


@pytest.mark.parametrize("field", [
    "runtime_may_auto_prioritize_sources",
    "runtime_may_auto_merge_identity",
    "runtime_may_create_relationship_edge",
    "runtime_may_create_evidence_edge",
    "runtime_may_delete_disfavored_assertions",
    "v386_resolution_is_truth_verdict",
    "identity_graph_mutation_performed",
    "relationship_graph_mutation_performed",
    "evidence_graph_mutation_performed",
])
def test_contract_boundaries_false(field):
    assert contract_document()["boundaries"][field] is False


def test_identity_conflict_remains_partially_resolved():
    s = ref().contradiction_sets[0]
    d = ref().decisions[0]
    assert s.contradiction_domain == ContradictionDomain.identity
    assert s.state == ResolutionState.partially_resolved
    assert d.state == ResolutionState.partially_resolved
    assert d.decision_does_not_mutate_identity_graph is True


def test_relationship_resolution_narrows_scope_for_handoff():
    s = ref().contradiction_sets[1]
    d = ref().decisions[1]
    assert s.contradiction_domain == ContradictionDomain.relationship
    assert s.state == ResolutionState.resolved_for_handoff
    assert d.state == ResolutionState.resolved_for_handoff
    assert len(d.favored_assertion_refs) == 1
    assert len(d.qualified_assertion_refs) == 1


def test_all_assertions_preserve_nontruth_boundary():
    for a in ref().assertions:
        assert a.assertion_is_not_truth_verdict is True
        assert a.confidence_is_not_probability_of_truth is True
        assert a.assertion_does_not_create_graph_edge is True


def test_all_sets_preserve_disagreement():
    for s in ref().contradiction_sets:
        assert s.contradiction_is_not_falsity_verdict is True
        assert s.unresolved_does_not_imply_equal_evidentiary_support is True
        assert s.source_disagreement_is_preserved is True


def test_all_criteria_are_non_dispositive():
    for c in ref().criterion_assessments:
        assert c.criterion_is_not_truth_test is True
        assert c.criterion_does_not_create_source_precedence is True
        assert c.basis_refs


def test_all_reviews_are_independent_nontruth():
    reviewers = set()
    for r in ref().reviews:
        assert r.independent_review is True
        assert r.review_is_not_truth_verdict is True
        assert r.review_does_not_mutate_graphs is True
        reviewers.add(r.reviewer_ref)
    assert len(reviewers) == 4


def test_all_decisions_preserve_assertions():
    for d in ref().decisions:
        assert set(d.favored_assertion_refs + d.qualified_assertion_refs).issubset(set(d.preserved_assertion_refs))
        assert d.decision_is_not_truth_verdict is True
        assert d.decision_does_not_delete_source_assertions is True
        assert d.decision_does_not_rewrite_historical_source_state is True


def test_supersession_preserves_history():
    s = ref().supersessions[0]
    assert s.supersession_does_not_delete_history is True
    assert s.supersession_does_not_make_prior_source_false is True
    assert s.superseded_assertion_ref != s.replacement_or_qualifying_assertion_ref


def test_handoffs_require_downstream_validation():
    targets = {h.target for h in ref().handoffs}
    assert targets == {HandoffTarget.identity_resolution, HandoffTarget.relationship_validation}
    for h in ref().handoffs:
        assert h.handoff_is_not_graph_mutation is True
        assert h.downstream_validation_required is True


def test_snapshot_is_immutable_and_preserving():
    s = ref().snapshots[0]
    assert s.immutable_snapshot is True
    assert s.snapshot_preserves_conflicting_assertions is True
    assert s.snapshot_preserves_resolution_lineage is True
    assert s.snapshot_is_not_truth_verdict is True
    assert s.snapshot_does_not_mutate_graphs is True


def test_upstream_reasoning_snapshot_reference_resolves():
    b = ref()
    ids = {x.reasoning_snapshot_id for x in b.multi_hop_research_investigation_graph_reasoning_bundle.snapshots}
    assert b.snapshots[0].multi_hop_reasoning_snapshot_ref in ids


def test_schema_generation():
    schema = type(ref()).model_json_schema()
    assert schema["title"] == "ContradictoryIdentityRelationshipResolutionBundle"
    assert "$defs" in schema


@pytest.mark.parametrize("idx,domain", [(0,"identity"),(1,"identity"),(2,"relationship"),(3,"relationship")])
def test_assertion_domains(idx, domain):
    assert ref().assertions[idx].contradiction_domain.value == domain


@pytest.mark.parametrize("idx,position", [(0,"supports"),(1,"qualifies"),(2,"supports"),(3,"qualifies")])
def test_assertion_positions(idx, position):
    assert ref().assertions[idx].position.value == position


@pytest.mark.parametrize("idx", range(4))
def test_assertions_have_upstream_refs(idx):
    assert ref().assertions[idx].upstream_object_refs


@pytest.mark.parametrize("idx", range(4))
def test_assertions_have_provenance(idx):
    assert ref().assertions[idx].provenance_refs


@pytest.mark.parametrize("idx", range(4))
def test_assertion_fingerprints_stable(idx):
    a=ref().assertions[idx]
    assert a.fingerprint() == a.fingerprint()
    assert len(a.fingerprint()) == 64


@pytest.mark.parametrize("idx", range(4))
def test_criteria_have_rationale(idx):
    assert len(ref().criterion_assessments[idx].rationale) > 20


@pytest.mark.parametrize("idx", range(4))
def test_reviews_consider_two_assertions(idx):
    assert len(ref().reviews[idx].considered_assertion_refs) == 2


@pytest.mark.parametrize("idx", range(2))
def test_decisions_have_two_reviews(idx):
    assert len(ref().decisions[idx].review_refs) == 2


@pytest.mark.parametrize("idx", range(2))
def test_decisions_have_criteria(idx):
    assert len(ref().decisions[idx].criterion_assessment_refs) == 2


@pytest.mark.parametrize("idx", range(2))
def test_sets_have_two_assertions(idx):
    assert len(ref().contradiction_sets[idx].assertion_refs) == 2


@pytest.mark.parametrize("field", [
    "majority_agreement_can_establish_truth",
    "source_count_can_establish_truth",
    "recency_can_establish_truth",
    "model_confidence_can_establish_truth",
    "automatic_source_precedence_allowed",
    "automatic_graph_mutation_allowed",
])
def test_policy_disallows_shortcuts(field):
    assert getattr(ref().policies[0], field) is False


@pytest.mark.parametrize("field", [
    "require_source_provenance",
    "require_temporal_context",
    "require_source_independence_accounting",
    "require_explicit_criterion_assessments",
    "preserve_disfavored_assertion_lineage",
    "preserve_unresolved_conflicts",
])
def test_policy_requires_governance(field):
    assert getattr(ref().policies[0], field) is True


@pytest.mark.parametrize("n", [1,2,3,4,5,10,20])
def test_policy_valid_reviewer_minimum(n):
    p=ContradictionResolutionPolicy(resolution_policy_id=f"policy:{n}", minimum_independent_reviewers=n)
    assert p.minimum_independent_reviewers == n


@pytest.mark.parametrize("n", [0,21,-1,100])
def test_policy_invalid_reviewer_minimum(n):
    with pytest.raises(ValidationError):
        ContradictionResolutionPolicy(resolution_policy_id="policy:x", minimum_independent_reviewers=n)


def test_duplicate_subject_refs_rejected():
    a=ref().assertions[0].model_dump(mode="python")
    a["subject_refs"] = a["subject_refs"] + [a["subject_refs"][0]]
    with pytest.raises(ValidationError): ContradictoryAssertionRecord(**a)


def test_confidence_requires_semantics():
    a=ref().assertions[0].model_dump(mode="python")
    a["confidence_semantics"] = None
    with pytest.raises(ValidationError): ContradictoryAssertionRecord(**a)


def test_contradiction_set_requires_two_assertions():
    s=ref().contradiction_sets[0].model_dump(mode="python")
    s["assertion_refs"] = [s["assertion_refs"][0]]
    with pytest.raises(ValidationError): ContradictionSet(**s)


def test_decision_cannot_drop_favored_assertion_from_preservation():
    d=ref().decisions[1].model_dump(mode="python")
    d["preserved_assertion_refs"] = [d["qualified_assertion_refs"][0]]
    with pytest.raises(ValidationError): ContradictionResolutionDecision(**d)


def test_bundle_rejects_unknown_set_assertion_ref():
    data=ref().model_dump(mode="python")
    data["contradiction_sets"][0]["assertion_refs"][0]="assertion:missing"
    with pytest.raises(ValidationError): type(ref())(**data)


def test_bundle_rejects_unknown_criterion_assertion_ref():
    data=ref().model_dump(mode="python")
    data["criterion_assessments"][0]["assertion_ref"]="assertion:missing"
    with pytest.raises(ValidationError): type(ref())(**data)


def test_bundle_rejects_unknown_review_criterion_ref():
    data=ref().model_dump(mode="python")
    data["reviews"][0]["considered_criterion_assessment_refs"]=["criterion:missing"]
    with pytest.raises(ValidationError): type(ref())(**data)


def test_bundle_rejects_unknown_decision_review_ref():
    data=ref().model_dump(mode="python")
    data["decisions"][1]["review_refs"]=["review:missing-a","review:missing-b"]
    with pytest.raises(ValidationError): type(ref())(**data)


def test_bundle_rejects_insufficient_resolved_reviewers():
    data=ref().model_dump(mode="python")
    data["decisions"][1]["review_refs"]=[data["decisions"][1]["review_refs"][0]]
    with pytest.raises(ValidationError): type(ref())(**data)


def test_bundle_rejects_unknown_supersession_assertion():
    data=ref().model_dump(mode="python")
    data["supersessions"][0]["superseded_assertion_ref"]="assertion:missing"
    with pytest.raises(ValidationError): type(ref())(**data)


def test_bundle_rejects_unknown_handoff_decision():
    data=ref().model_dump(mode="python")
    data["handoffs"][0]["resolution_decision_ref"]="decision:missing"
    with pytest.raises(ValidationError): type(ref())(**data)


def test_bundle_rejects_unknown_upstream_snapshot():
    data=ref().model_dump(mode="python")
    data["snapshots"][0]["multi_hop_reasoning_snapshot_ref"]="reasoning-snapshot:missing"
    with pytest.raises(ValidationError): type(ref())(**data)


@pytest.mark.parametrize("domain", [x.value for x in ContradictionDomain])
def test_domain_round_trip(domain):
    assert ContradictionDomain(domain).value == domain


@pytest.mark.parametrize("position", [x.value for x in AssertionPosition])
def test_position_round_trip(position):
    assert AssertionPosition(position).value == position


@pytest.mark.parametrize("state", [x.value for x in ResolutionState])
def test_resolution_state_round_trip(state):
    assert ResolutionState(state).value == state


@pytest.mark.parametrize("target", [x.value for x in HandoffTarget])
def test_handoff_target_round_trip(target):
    assert HandoffTarget(target).value == target


def test_contract_reference_fingerprint_matches_bundle():
    assert contract_document()["reference"]["bundle_fingerprint_sha256"] == ref().fingerprint()
