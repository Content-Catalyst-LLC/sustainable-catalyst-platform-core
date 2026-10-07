#!/usr/bin/env python3
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
def check(label, cond):
    if not cond: raise SystemExit(f"{label}=FAIL")
    print(f"{label}=PASS")
config=(ROOT/'backend/app/config.py').read_text(); main=(ROOT/'backend/app/main.py').read_text(); service=(ROOT/'backend/app/services/evidence_context_integration.py').read_text(); router=(ROOT/'backend/app/routers/evidence_context_integration.py').read_text(); readme=(ROOT/'README.md').read_text(); wp=(ROOT/'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text(); wpread=(ROOT/'wordpress-plugin/sustainable-catalyst-platform-core/readme.txt').read_text(); v413v=(ROOT/'scripts/validate_v4130_release.py').read_text()
m=re.search(r'version: str = \"(\d+)\.(\d+)\.(\d+)\"', config); check('PLATFORM_CORE_V4140_BACKEND_VERSION', bool(m) and tuple(map(int,m.groups())) >= (4,14,0))
check('PLATFORM_CORE_V4140_ROUTE_MOUNT','evidence_context_integration.router' in main and 'evidence_context_integration.public_router' in main)
check('PLATFORM_CORE_V4140_SERVICE_RELEASE','CORE_RELEASE = "4.14.0"' in service)
check('PLATFORM_CORE_V4140_CONTRACT','sc.core.evidence-context-integration-layer.v1' in service)
check('PLATFORM_CORE_V4140_API_SURFACE','/v1/evidence-context' in router and '/public/v1/evidence-context' in router)
check('PLATFORM_CORE_V4140_EVIDENCE_ANCHOR_FOUNDATION',all(x in service for x in ['EvidenceGraphAnchor','EvidenceIndependenceState','upstream_review_status_remains_authoritative']))
check('PLATFORM_CORE_V4140_LINK_FOUNDATION',all(x in service for x in ['EvidenceContextLink','EvidenceContextRelationKind','link_is_interpretive_bridge_not_evidence_review']))
check('PLATFORM_CORE_V4140_ASSESSMENT_FOUNDATION',all(x in service for x in ['EvidenceContextAssessment','EvidenceIntegrationOutcome','unresolved_evidence_conflict']))
check('PLATFORM_CORE_V4140_PROVENANCE_SNAPSHOT',all(x in service for x in ['EvidenceContextProvenanceRecord','EvidenceContextSnapshot','deterministic_integration_fingerprint_sha256']))
check('PLATFORM_CORE_V4140_EPISTEMIC_BOUNDARY',all(x in service for x in ['supporting_evidence_count_establishes_truth','evidence_link_establishes_evidence_validity','contradiction_link_identifies_false_claim','semantic_layer_may_override_upstream_review_status']))
check('PLATFORM_CORE_V4140_MUTATION_BOUNDARY',all(x in service for x in ['automatic_evidence_materialization_authorized','context_graph_mutation_authorized','identity_graph_mutation_authorized','evidence_graph_mutation_authorized','knowledge_graph_mutation_authorized']))
check('PLATFORM_CORE_V4140_DERIVED_EVIDENCE_BOUNDARY','translation_derivative_is_not_independent_corroboration' in service and 'same_source_derived' in service)
check('PLATFORM_CORE_V4140_README','v4.14.0 — Evidence-Context Integration Layer' in readme)
wm=re.search(r'Version: (\d+)\.(\d+)\.(\d+)', wp); sm=re.search(r"SCPC_VERSION', '(\d+)\.(\d+)\.(\d+)", wp); check('PLATFORM_CORE_V4140_WORDPRESS_VERSION', bool(wm and sm) and tuple(map(int,wm.groups())) >= (4,14,0) and tuple(map(int,sm.groups())) >= (4,14,0))
stm=re.search(r'Stable tag: (\d+)\.(\d+)\.(\d+)', wpread); check('PLATFORM_CORE_V4140_WORDPRESS_STABLE_TAG', bool(stm) and tuple(map(int,stm.groups())) >= (4,14,0))
check('PLATFORM_CORE_V4140_SCHEMA',(ROOT/'schemas/sc-core-evidence-context-integration-layer-v1.schema.json').exists())
check('PLATFORM_CORE_V4140_TEST_COVERAGE',(ROOT/'backend/tests/test_evidence_context_integration_v4140.py').exists())
check('PLATFORM_CORE_V4140_V413_FORWARD_COMPATIBILITY',">= (4, 13, 0)" in v413v)
check('PLATFORM_CORE_V4140_NO_DB_MIGRATION','database_migration: Literal["none"]' in service)
print('PLATFORM_CORE_V4140_VALIDATION=PASS')
