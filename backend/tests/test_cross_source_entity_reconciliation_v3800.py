import pytest
from pydantic import ValidationError

from app.services.cross_source_entity_reconciliation import (
    CONTRACT_VERSION,
    CrossSourceComparisonObservation,
    CrossSourceEntityReconciliationBundle,
    CrossSourceEntityReconciliationCluster,
    CrossSourceReconciliationDecision,
    CrossSourceReconciliationPolicy,
    IdentityProvenanceChain,
    ReconciliationSourceDescriptor,
    SourceIdentityObservation,
    contract_document,
    reference_cross_source_entity_reconciliation_bundle,
)


def ref():
    return reference_cross_source_entity_reconciliation_bundle()


def test_release(): assert contract_document()["release"] == "3.80.0"
def test_contract(): assert contract_document()["contract"] == CONTRACT_VERSION
def test_extends_v377(): assert "sc.core.entity-resolution-identity-graph-foundation.v1" in contract_document()["extends_contracts"]
def test_extends_v378(): assert "sc.core.temporal-identity-alias-name-variant-intelligence.v1" in contract_document()["extends_contracts"]
def test_extends_v379(): assert "sc.core.probabilistic-record-linkage-entity-matching.v1" in contract_document()["extends_contracts"]
def test_three_source_descriptors(): assert len(ref().source_descriptors) == 3
def test_three_source_observations(): assert len(ref().source_observations) == 3
def test_two_comparisons(): assert len(ref().comparisons) == 2
def test_two_provenance_chains(): assert len(ref().provenance_chains) == 2
def test_one_conflict(): assert len(ref().conflicts) == 1
def test_one_cluster(): assert len(ref().clusters) == 1
def test_one_policy(): assert len(ref().policies) == 1
def test_two_reviews(): assert len(ref().reviews) == 2
def test_one_decision(): assert len(ref().decisions) == 1
def test_one_snapshot(): assert len(ref().provenance_snapshots) == 1
def test_decision_candidate_supported(): assert ref().decisions[0].decision_state.value == "candidate-supported"
def test_cluster_source_aligned_candidate(): assert ref().clusters[0].cluster_state.value == "source-aligned-candidate"
def test_source_agreement_not_fact_bundle(): assert ref().source_agreement_is_not_identity_fact is True
def test_source_count_not_evidence_bundle(): assert ref().source_count_is_not_identity_evidence is True
def test_no_auto_precedence_bundle(): assert ref().automatic_source_precedence_allowed is False
def test_no_canonical_merge_bundle(): assert ref().canonical_identity_merge_performed is False
def test_no_identity_mutation_bundle(): assert ref().identity_graph_mutation_performed is False
def test_descriptor_not_trust_verdict(): assert all(x.source_descriptor_is_not_trust_verdict for x in ref().source_descriptors)
def test_descriptor_independence_explicit(): assert all(x.source_independence_must_be_evaluated_explicitly for x in ref().source_descriptors)
def test_observation_not_canonical(): assert all(x.source_observation_is_not_canonical_identity for x in ref().source_observations)
def test_observation_no_override(): assert all(x.source_observation_does_not_override_other_sources for x in ref().source_observations)
def test_comparison_agreement_not_fact(): assert all(x.source_agreement_is_not_identity_fact for x in ref().comparisons)
def test_comparison_disagreement_not_nonidentity_fact(): assert all(x.source_disagreement_is_not_nonidentity_fact for x in ref().comparisons)
def test_probability_context_only(): assert all(x.linkage_probability_is_context_only for x in ref().comparisons)
def test_chain_not_identity_proof(): assert all(x.provenance_chain_is_not_identity_proof for x in ref().provenance_chains)
def test_chain_completeness_not_truth(): assert all(x.completeness_is_not_truth for x in ref().provenance_chains)
def test_conflict_preserves_sources(): assert ref().conflicts[0].conflicting_sources_are_preserved is True
def test_conflict_no_precedence(): assert ref().conflicts[0].no_automatic_source_precedence is True
def test_conflict_not_distinct_identity_proof(): assert ref().conflicts[0].conflict_is_not_proof_of_distinct_identity is True
def test_cluster_membership_not_fact(): assert ref().clusters[0].cluster_membership_is_not_identity_fact is True
def test_cluster_not_equivalence(): assert ref().clusters[0].cluster_is_not_canonical_equivalence is True
def test_cluster_does_not_merge(): assert ref().clusters[0].cluster_does_not_merge_entities is True
def test_policy_requires_provenance(): assert ref().policies[0].require_provenance_chain is True
def test_policy_requires_review(): assert ref().policies[0].require_independent_review is True
def test_policy_two_source_groups(): assert ref().policies[0].minimum_independent_source_groups == 2
def test_policy_preserves_disagreement(): assert ref().policies[0].preserve_source_disagreement is True
def test_policy_no_source_precedence(): assert ref().policies[0].automatic_source_precedence_allowed is False
def test_policy_source_count_no_gate(): assert ref().policies[0].source_count_can_satisfy_identity_gate is False
def test_policy_probability_no_gate(): assert ref().policies[0].linkage_probability_can_satisfy_identity_gate is False
def test_policy_agreement_no_gate(): assert ref().policies[0].source_agreement_can_satisfy_identity_gate is False
def test_review_probability_context(): assert all(x.probability_is_context_not_identity_evidence for x in ref().reviews)
def test_review_no_merge(): assert all(x.review_does_not_merge_entities for x in ref().reviews)
def test_decision_not_canonical(): assert ref().decisions[0].decision_is_not_canonical_identity is True
def test_decision_no_edge(): assert ref().decisions[0].decision_does_not_create_equivalence_edge is True
def test_decision_no_merge(): assert ref().decisions[0].decision_does_not_merge_entities is True
def test_decision_v377_required(): assert ref().decisions[0].downstream_v377_identity_resolution_required is True
def test_snapshot_immutable(): assert ref().provenance_snapshots[0].immutable_snapshot is True
def test_snapshot_preserves_sources(): assert ref().provenance_snapshots[0].source_specific_assertions_preserved is True
def test_snapshot_no_mutation(): assert ref().provenance_snapshots[0].snapshot_does_not_mutate_identity_graph is True
def test_snapshot_not_truth(): assert ref().provenance_snapshots[0].snapshot_is_not_identity_truth is True
def test_reference_fingerprint_stable(): assert ref().fingerprint() == ref().fingerprint()
def test_reference_fingerprint_64(): assert len(ref().fingerprint()) == 64
def test_contract_fingerprint_64(): assert len(contract_document()["reference"]["bundle_fingerprint_sha256"]) == 64
def test_independent_source_groups_two(): assert contract_document()["reference"]["independent_source_group_count"] == 2


def test_observation_requires_upstream_assertion():
    d = ref().source_observations[0].model_dump()
    d["source_identity_assertion_ref"] = None
    d["temporal_source_assertion_ref"] = None
    with pytest.raises(ValidationError): SourceIdentityObservation.model_validate(d)


def test_comparison_self_reference_rejected():
    d = ref().comparisons[0].model_dump()
    d["right_observation_ref"] = d["left_observation_ref"]
    with pytest.raises(ValidationError): CrossSourceComparisonObservation.model_validate(d)


def test_comparison_field_subset_enforced():
    d = ref().comparisons[0].model_dump()
    d["agreement_fields"] = ["not-compared"]
    with pytest.raises(ValidationError): CrossSourceComparisonObservation.model_validate(d)


def test_complete_chain_cannot_have_missing_links():
    d = ref().provenance_chains[0].model_dump()
    d["missing_link_notes"] = ["missing"]
    with pytest.raises(ValidationError): IdentityProvenanceChain.model_validate(d)


def test_supported_decision_requires_evidence():
    d = ref().decisions[0].model_dump()
    d["identity_evidence_refs"] = []
    with pytest.raises(ValidationError): CrossSourceReconciliationDecision.model_validate(d)


def test_supported_decision_requires_reviews():
    d = ref().decisions[0].model_dump()
    d["review_refs"] = []
    with pytest.raises(ValidationError): CrossSourceReconciliationDecision.model_validate(d)


def test_supported_decision_requires_v377_candidate():
    d = ref().decisions[0].model_dump()
    d["v377_candidate_match_ref"] = None
    with pytest.raises(ValidationError): CrossSourceReconciliationDecision.model_validate(d)


def test_unknown_observation_source_descriptor_rejected():
    b = ref().model_copy(deep=True)
    b.source_observations[0].source_descriptor_ref = "source-descriptor:missing"
    with pytest.raises(ValidationError): CrossSourceEntityReconciliationBundle.model_validate(b.model_dump(mode="json"))


def test_unknown_observation_entity_rejected():
    b = ref().model_copy(deep=True)
    b.source_observations[0].entity_ref = "entity:missing"
    with pytest.raises(ValidationError): CrossSourceEntityReconciliationBundle.model_validate(b.model_dump(mode="json"))


def test_unknown_source_assertion_rejected():
    b = ref().model_copy(deep=True)
    b.source_observations[0].source_identity_assertion_ref = "source-identity:missing"
    with pytest.raises(ValidationError): CrossSourceEntityReconciliationBundle.model_validate(b.model_dump(mode="json"))


def test_unknown_temporal_assertion_rejected():
    b = ref().model_copy(deep=True)
    b.source_observations[2].temporal_source_assertion_ref = "temporal-source:missing"
    with pytest.raises(ValidationError): CrossSourceEntityReconciliationBundle.model_validate(b.model_dump(mode="json"))


def test_unknown_comparison_observation_rejected():
    b = ref().model_copy(deep=True)
    b.comparisons[0].left_observation_ref = "observation:missing"
    with pytest.raises(ValidationError): CrossSourceEntityReconciliationBundle.model_validate(b.model_dump(mode="json"))


def test_unknown_comparison_probability_rejected():
    b = ref().model_copy(deep=True)
    b.comparisons[0].linkage_probability_ref = "probability:missing"
    with pytest.raises(ValidationError): CrossSourceEntityReconciliationBundle.model_validate(b.model_dump(mode="json"))


def test_unknown_chain_observation_rejected():
    b = ref().model_copy(deep=True)
    b.provenance_chains[0].source_observation_refs = ["observation:missing"]
    with pytest.raises(ValidationError): CrossSourceEntityReconciliationBundle.model_validate(b.model_dump(mode="json"))


def test_unknown_conflict_chain_rejected():
    b = ref().model_copy(deep=True)
    b.conflicts[0].provenance_chain_refs = ["chain:missing"]
    with pytest.raises(ValidationError): CrossSourceEntityReconciliationBundle.model_validate(b.model_dump(mode="json"))


def test_unknown_cluster_candidate_rejected():
    b = ref().model_copy(deep=True)
    b.clusters[0].candidate_match_refs = ["candidate:missing"]
    with pytest.raises(ValidationError): CrossSourceEntityReconciliationBundle.model_validate(b.model_dump(mode="json"))


def test_unknown_cluster_pairwise_decision_rejected():
    b = ref().model_copy(deep=True)
    b.clusters[0].pairwise_match_decision_refs = ["decision:missing"]
    with pytest.raises(ValidationError): CrossSourceEntityReconciliationBundle.model_validate(b.model_dump(mode="json"))


def test_unknown_cluster_temporal_snapshot_rejected():
    b = ref().model_copy(deep=True)
    b.clusters[0].temporal_snapshot_refs = ["snapshot:missing"]
    with pytest.raises(ValidationError): CrossSourceEntityReconciliationBundle.model_validate(b.model_dump(mode="json"))


def test_unknown_review_evidence_rejected():
    b = ref().model_copy(deep=True)
    b.reviews[0].identity_evidence_refs = ["evidence:missing"]
    with pytest.raises(ValidationError): CrossSourceEntityReconciliationBundle.model_validate(b.model_dump(mode="json"))


def test_unknown_decision_policy_rejected():
    b = ref().model_copy(deep=True)
    b.decisions[0].reconciliation_policy_ref = "policy:missing"
    with pytest.raises(ValidationError): CrossSourceEntityReconciliationBundle.model_validate(b.model_dump(mode="json"))


def test_unknown_decision_review_rejected():
    b = ref().model_copy(deep=True)
    b.decisions[0].review_refs = ["review:missing"]
    with pytest.raises(ValidationError): CrossSourceEntityReconciliationBundle.model_validate(b.model_dump(mode="json"))


def test_duplicate_source_ref_rejected():
    b = ref().model_copy(deep=True)
    b.source_descriptors[1].source_ref = b.source_descriptors[0].source_ref
    with pytest.raises(ValidationError): CrossSourceEntityReconciliationBundle.model_validate(b.model_dump(mode="json"))


def test_contract_no_fetch(): assert contract_document()["boundaries"]["core_fetches_or_scrapes_sources"] is False
def test_contract_no_source_priority(): assert contract_document()["boundaries"]["core_auto_prioritizes_one_source_over_another"] is False
def test_contract_no_source_count_evidence(): assert contract_document()["boundaries"]["core_treats_source_count_as_identity_evidence"] is False
def test_contract_no_source_agreement_fact(): assert contract_document()["boundaries"]["core_treats_source_agreement_as_identity_fact"] is False
def test_contract_no_probability_evidence(): assert contract_document()["boundaries"]["core_treats_linkage_probability_as_identity_evidence"] is False
def test_contract_no_conflict_auto_resolution(): assert contract_document()["boundaries"]["core_auto_resolves_source_conflicts"] is False
def test_contract_no_auto_merge(): assert contract_document()["boundaries"]["core_auto_merges_reconciled_entities"] is False
def test_contract_no_graph_mutation(): assert contract_document()["boundaries"]["core_mutates_identity_graph_during_reconciliation"] is False
def test_contract_no_v377_bypass(): assert contract_document()["boundaries"]["core_bypasses_v377_identity_resolution_policy"] is False
def test_contract_prepares_v381(): assert contract_document()["roadmap_integration"]["prepares_v3810_public_record_documentary_source_object_model"] is True
def test_contract_prepares_v382(): assert contract_document()["roadmap_integration"]["prepares_v3820_relationship_discovery_connection_hypotheses"] is True
