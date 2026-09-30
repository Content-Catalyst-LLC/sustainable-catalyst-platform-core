from app.services.cross_source_entity_reconciliation import (
    CONTRACT_VERSION,
    contract_document,
    reference_cross_source_entity_reconciliation_bundle,
)

b = reference_cross_source_entity_reconciliation_bundle()
c = contract_document()
assert c["contract"] == CONTRACT_VERSION
assert c["release"] == "3.80.0"
assert len(b.source_descriptors) == 3
assert len(b.source_observations) == 3
assert len(b.comparisons) == 2
assert len(b.provenance_chains) == 2
assert len(b.conflicts) == 1
assert len(b.clusters) == 1
assert len(b.reviews) == 2
assert len(b.decisions) == 1
assert b.decisions[0].decision_state.value == "candidate-supported"
assert b.source_agreement_is_not_identity_fact is True
assert b.source_count_is_not_identity_evidence is True
assert b.automatic_source_precedence_allowed is False
assert b.canonical_identity_merge_performed is False
assert b.identity_graph_mutation_performed is False
assert c["boundaries"]["core_auto_merges_reconciled_entities"] is False
assert c["boundaries"]["core_mutates_identity_graph_during_reconciliation"] is False
print("PASS - Platform Core v3.80.0 Cross-Source Entity Reconciliation & Identity Provenance")
print(f"CONTRACT={CONTRACT_VERSION}")
print(f"SOURCE_DESCRIPTORS={len(b.source_descriptors)}")
print(f"SOURCE_OBSERVATIONS={len(b.source_observations)}")
print(f"COMPARISONS={len(b.comparisons)}")
print(f"PROVENANCE_CHAINS={len(b.provenance_chains)}")
print(f"CONFLICTS={len(b.conflicts)}")
print(f"INDEPENDENT_SOURCE_GROUPS={len({x.independence_group for x in b.source_descriptors})}")
print(f"REVIEWS={len(b.reviews)}")
print(f"DECISION_STATE={b.decisions[0].decision_state.value}")
print("SOURCE_AGREEMENT_IS_IDENTITY_FACT=false")
print("SOURCE_COUNT_IS_IDENTITY_EVIDENCE=false")
print("CANONICAL_IDENTITY_MERGE_PERFORMED=false")
print("IDENTITY_GRAPH_MUTATION_PERFORMED=false")
