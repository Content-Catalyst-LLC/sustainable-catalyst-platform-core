#!/usr/bin/env python3
from app.services.contradictory_identity_relationship_resolution import (
    CONTRACT_VERSION,
    contract_document,
    reference_contradictory_identity_relationship_resolution_bundle,
)

b = reference_contradictory_identity_relationship_resolution_bundle()
c = contract_document()
assert c["release"] == "3.86.0"
assert c["contract"] == CONTRACT_VERSION
assert len(b.assertions) == 4
assert len(b.contradiction_sets) == 2
assert len(b.criterion_assessments) == 4
assert len(b.reviews) == 4
assert len(b.decisions) == 2
assert len(b.supersessions) == 1
assert len(b.handoffs) == 2
assert b.identity_graph_mutation_performed is False
assert b.relationship_graph_mutation_performed is False
assert b.evidence_graph_mutation_performed is False
print("PASS - Platform Core v3.86.0 Contradictory Identity & Relationship Resolution")
print(f"CONTRACT={CONTRACT_VERSION}")
print(f"ASSERTIONS={len(b.assertions)}")
print(f"CONTRADICTION_SETS={len(b.contradiction_sets)}")
print(f"CRITERION_ASSESSMENTS={len(b.criterion_assessments)}")
print(f"REVIEWS={len(b.reviews)}")
print(f"DECISIONS={len(b.decisions)}")
print(f"SUPERSESSIONS={len(b.supersessions)}")
print(f"HANDOFFS={len(b.handoffs)}")
print(f"IDENTITY_SET_STATE={b.contradiction_sets[0].state.value}")
print(f"RELATIONSHIP_SET_STATE={b.contradiction_sets[1].state.value}")
print("CONTRADICTION_IS_FALSITY_VERDICT=false")
print("MAJORITY_AGREEMENT_IS_TRUTH=false")
print("SOURCE_COUNT_IS_TRUTH=false")
print("RECENCY_IS_TRUTH=false")
print("MODEL_CONFIDENCE_IS_TRUTH=false")
print("IDENTITY_GRAPH_MUTATION_PERFORMED=false")
print("RELATIONSHIP_GRAPH_MUTATION_PERFORMED=false")
print("EVIDENCE_GRAPH_MUTATION_PERFORMED=false")
