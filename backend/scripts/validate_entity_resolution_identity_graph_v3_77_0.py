#!/usr/bin/env python3
from app.services.entity_resolution_identity_graph import (
    CORE_RELEASE,
    CONTRACT_VERSION,
    contract_document,
    reference_entity_resolution_identity_graph_bundle,
)

b = reference_entity_resolution_identity_graph_bundle()
c = contract_document()
a = b.mutation_authorizations[0]
assert CORE_RELEASE == "3.77.0"
assert CONTRACT_VERSION == "sc.core.entity-resolution-identity-graph-foundation.v1"
assert c["principles"]["match_probability_is_not_identity_fact"] is True
assert c["principles"]["automated_resolution_may_not_silently_merge_entities"] is True
assert c["principles"]["authorization_is_not_identity_graph_mutation"] is True
assert c["boundaries"]["core_auto_merges_entities_from_match_score"] is False
assert c["boundaries"]["core_mutates_identity_graph_during_authorization"] is False
assert a.actual_identity_graph_mutation_performed is False
print("PASS - Platform Core v3.77.0 Entity Resolution & Identity Graph Foundation")
print(f"CONTRACT={CONTRACT_VERSION}")
print(f"ENTITIES={len(b.entities)}")
print(f"ALIASES={len(b.aliases)}")
print(f"IDENTIFIER_ASSERTIONS={len(b.identifier_assertions)}")
print(f"SOURCE_IDENTITY_ASSERTIONS={len(b.source_identity_assertions)}")
print(f"CANDIDATE_MATCHES={len(b.candidate_matches)}")
print(f"INDEPENDENT_REVIEWERS={len({x.reviewer_ref for x in b.identity_reviews})}")
print(f"MERGE_DECISION={a.decision.value}")
print("MATCH_PROBABILITY_IS_IDENTITY_FACT=false")
print("AUTOMATED_RESOLUTION_MAY_SILENTLY_MERGE=false")
print("ACTUAL_IDENTITY_GRAPH_MUTATION_PERFORMED=false")
