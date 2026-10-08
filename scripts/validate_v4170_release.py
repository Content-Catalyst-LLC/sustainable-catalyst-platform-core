#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

def check(label, cond):
    if not cond:
        raise SystemExit(f"{label}=FAIL")
    print(f"{label}=PASS")

config=(ROOT/'backend/app/config.py').read_text()
main=(ROOT/'backend/app/main.py').read_text()
service=(ROOT/'backend/app/services/cross_source_semantic_reconciliation.py').read_text()
router=(ROOT/'backend/app/routers/cross_source_semantic_reconciliation.py').read_text()
readme=(ROOT/'README.md').read_text()
wp=(ROOT/'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text()
wpread=(ROOT/'wordpress-plugin/sustainable-catalyst-platform-core/readme.txt').read_text()
v416v=(ROOT/'scripts/validate_v4160_release.py').read_text()
_version_match=re.search(r'version: str = \"(\d+)\.(\d+)\.(\d+)\"', config)
_app_version=tuple(map(int,_version_match.groups())) if _version_match else (0,0,0)
check('PLATFORM_CORE_V4170_BACKEND_VERSION',_app_version >= (4,17,0))
check('PLATFORM_CORE_V4170_ROUTE_MOUNT','cross_source_semantic_reconciliation.router' in main and 'cross_source_semantic_reconciliation.public_router' in main)
check('PLATFORM_CORE_V4170_SERVICE_RELEASE','CORE_RELEASE = "4.17.0"' in service)
check('PLATFORM_CORE_V4170_CONTRACT','sc.core.cross-source-semantic-reconciliation-engine.v1' in service)
check('PLATFORM_CORE_V4170_API_SURFACE','/v1/source-reconciliation' in router and '/public/v1/source-reconciliation' in router)
check('PLATFORM_CORE_V4170_ANCHOR_FOUNDATION',all(x in service for x in ['ReconciliationAnchor','ReconciliationAnchorKind','anchor_is_not_canonical_identity_or_truth']))
check('PLATFORM_CORE_V4170_CANDIDATE_FOUNDATION',all(x in service for x in ['SemanticCorrespondenceCandidate','ReconciliationRelation','candidate_establishes_equivalence']))
check('PLATFORM_CORE_V4170_CONFLICT_FOUNDATION',all(x in service for x in ['ReconciliationConflict','ReconciliationConflictKind','conflict_is_not_truth_adjudication']))
check('PLATFORM_CORE_V4170_DECISION_FOUNDATION',all(x in service for x in ['ReconciliationDecision','canonicalization_authorized','identity_merge_authorized']))
check('PLATFORM_CORE_V4170_CLUSTER_FOUNDATION',all(x in service for x in ['ReconciledSemanticCluster','cluster_is_navigation_object_not_canonical_entity']))
check('PLATFORM_CORE_V4170_PROVENANCE_SNAPSHOT',all(x in service for x in ['CrossSourceReconciliationProvenanceRecord','CrossSourceReconciliationSnapshot','deterministic_reconciliation_fingerprint_sha256']))
check('PLATFORM_CORE_V4170_EPISTEMIC_BOUNDARY',all(x in service for x in ['reconciliation_is_alignment_not_canonicalization','source_agreement_is_not_truth','temporal_overlap_is_not_same_event','derived_representation_is_not_independent_source']))
check('PLATFORM_CORE_V4170_MUTATION_BOUNDARY',all(x in service for x in ['automatic_canonical_entity_merge_authorized','automatic_context_graph_mutation_authorized','automatic_evidence_graph_mutation_authorized','automatic_knowledge_graph_mutation_authorized','automatic_identity_graph_mutation_authorized']))
check('PLATFORM_CORE_V4170_README','v4.17.0 — Cross-Source Semantic Reconciliation Engine' in readme)
_wp_version_match=re.search(r'Version: (\d+)\.(\d+)\.(\d+)', wp)
_wp_version=tuple(map(int,_wp_version_match.groups())) if _wp_version_match else (0,0,0)
check('PLATFORM_CORE_V4170_WORDPRESS_VERSION',_wp_version >= (4,17,0))
_wp_tag_match=re.search(r'Stable tag: (\d+)\.(\d+)\.(\d+)', wpread)
_wp_tag=tuple(map(int,_wp_tag_match.groups())) if _wp_tag_match else (0,0,0)
check('PLATFORM_CORE_V4170_WORDPRESS_STABLE_TAG',_wp_tag >= (4,17,0))
check('PLATFORM_CORE_V4170_SCHEMA',(ROOT/'schemas/sc-core-cross-source-semantic-reconciliation-engine-v1.schema.json').exists())
check('PLATFORM_CORE_V4170_TEST_COVERAGE',(ROOT/'backend/tests/test_cross_source_semantic_reconciliation_v4170.py').exists())
check('PLATFORM_CORE_V4170_V416_FORWARD_COMPATIBILITY','_app_version >= (4,16,0)' in v416v and '_wp_version >= (4,16,0)' in v416v and '_wp_tag >= (4,16,0)' in v416v)
check('PLATFORM_CORE_V4170_NO_DB_MIGRATION','database_migration: Literal["none"]' in service)
print('PLATFORM_CORE_V4170_VALIDATION=PASS')
