#!/usr/bin/env python3
from app.services.temporal_identity_intelligence import CORE_RELEASE, CONTRACT_VERSION, contract_document, reference_temporal_identity_intelligence_bundle

b = reference_temporal_identity_intelligence_bundle()
c = contract_document()
assert CORE_RELEASE == "3.78.0"
assert CONTRACT_VERSION == "sc.core.temporal-identity-alias-name-variant-intelligence.v1"
assert c["principles"]["same_name_across_time_is_not_identity_proof"] is True
assert c["principles"]["historical_role_does_not_establish_current_affiliation"] is True
assert c["principles"]["temporal_context_cannot_auto_merge_entities"] is True
assert c["boundaries"]["core_auto_resolves_temporal_conflicts"] is False
assert c["boundaries"]["core_auto_merges_entities_from_temporal_overlap"] is False
assert c["reference"]["identity_graph_mutation_performed"] is False
print("PASS - Platform Core v3.78.0 Temporal Identity, Alias & Name Variant Intelligence")
print(f"CONTRACT={CONTRACT_VERSION}")
print(f"TEMPORAL_NAMES={len(b.temporal_names)}")
print(f"TEMPORAL_IDENTIFIERS={len(b.temporal_identifiers)}")
print(f"TEMPORAL_ROLES={len(b.temporal_roles)}")
print(f"TEMPORAL_SOURCE_ASSERTIONS={len(b.temporal_source_assertions)}")
print(f"TEMPORAL_CONFLICTS={len(b.temporal_conflicts)}")
print(f"TEMPORAL_SNAPSHOTS={len(b.temporal_snapshots)}")
print("SAME_NAME_ACROSS_TIME_IS_IDENTITY_PROOF=false")
print("HISTORICAL_ROLE_ESTABLISHES_CURRENT_AFFILIATION=false")
print("TEMPORAL_CONTEXT_CAN_AUTO_MERGE=false")
print("IDENTITY_GRAPH_MUTATION_PERFORMED=false")
