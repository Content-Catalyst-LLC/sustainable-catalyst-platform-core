#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def check(label, cond):
    if not cond:
        raise SystemExit(f"{label}=FAIL")
    print(f"{label}=PASS")


config = (ROOT / 'backend/app/config.py').read_text()
main = (ROOT / 'backend/app/main.py').read_text()
service = (ROOT / 'backend/app/services/claim_alignment_agreement_contradiction.py').read_text()
router = (ROOT / 'backend/app/routers/claim_alignment_agreement_contradiction.py').read_text()
readme = (ROOT / 'README.md').read_text()
wp = (ROOT / 'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text()
wpread = (ROOT / 'wordpress-plugin/sustainable-catalyst-platform-core/readme.txt').read_text()
v412test = (ROOT / 'backend/tests/test_context_retrieval_relevance_v4120.py').read_text()
v412validator = (ROOT / 'scripts/validate_v4120_release.py').read_text()

m = re.search(r'version: str = "(\d+)\.(\d+)\.(\d+)"', config)
check('PLATFORM_CORE_V4130_BACKEND_VERSION', bool(m) and tuple(map(int, m.groups())) >= (4, 13, 0))
check('PLATFORM_CORE_V4130_ROUTE_MOUNT', 'claim_alignment_agreement_contradiction.router' in main and 'claim_alignment_agreement_contradiction.public_router' in main)
check('PLATFORM_CORE_V4130_SERVICE_RELEASE', 'CORE_RELEASE = "4.13.0"' in service)
check('PLATFORM_CORE_V4130_CONTRACT', 'sc.core.claim-alignment-agreement-contradiction-intelligence.v1' in service)
check('PLATFORM_CORE_V4130_API_SURFACE', '/v1/claim-comparison' in router and '/public/v1/claim-comparison' in router)
check('PLATFORM_CORE_V4130_CLAIM_FOUNDATION', all(x in service for x in ['ClaimSourceContext', 'ClaimUnit', 'ClaimComparisonQuery']))
check('PLATFORM_CORE_V4130_ALIGNMENT_FOUNDATION', all(x in service for x in ['ClaimAlignmentSignal', 'ClaimComparisonPair', 'AlignmentDimension']))
check('PLATFORM_CORE_V4130_RELATION_FOUNDATION', all(x in service for x in ['ClaimRelationAssessment', 'ClaimRelationKind', 'apparent_contradiction', 'qualified_agreement']))
check('PLATFORM_CORE_V4130_PROVENANCE_SNAPSHOT', all(x in service for x in ['ClaimComparisonProvenanceRecord', 'ClaimComparisonSnapshot', 'deterministic_comparison_fingerprint_sha256']))
check('PLATFORM_CORE_V4130_SCOPE_BOUNDARY', all(x in service for x in ['polarity_difference_alone_is_not_contradiction', 'modality_mismatch_may_downgrade_contradiction', 'temporal_and_spatial_scope_must_be_compared']))
check('PLATFORM_CORE_V4130_EPISTEMIC_BOUNDARY', all(x in service for x in ['reviewed_relation_establishes_truth', 'contradiction_identifies_false_claim', 'agreement_establishes_evidence_validity', 'source_majority_establishes_truth']))
check('PLATFORM_CORE_V4130_GRAPH_BOUNDARY', all(x in service for x in ['context_graph_mutation_authorized', 'identity_graph_mutation_authorized', 'evidence_graph_mutation_authorized', 'knowledge_graph_mutation_authorized']))
check('PLATFORM_CORE_V4130_README', 'v4.13.0 — Claim Alignment, Agreement & Contradiction Intelligence' in readme)
wpv = re.search(r'\* Version: (\d+)\.(\d+)\.(\d+)', wp)
scpcv = re.search(r"SCPC_VERSION', '(\d+)\.(\d+)\.(\d+)'", wp)
check('PLATFORM_CORE_V4130_WORDPRESS_VERSION', bool(wpv and scpcv) and tuple(map(int, wpv.groups())) >= (4, 13, 0) and tuple(map(int, scpcv.groups())) >= (4, 13, 0))
stable = re.search(r'Stable tag: (\d+)\.(\d+)\.(\d+)', wpread)
check('PLATFORM_CORE_V4130_WORDPRESS_STABLE_TAG', bool(stable) and tuple(map(int, stable.groups())) >= (4, 13, 0))
check('PLATFORM_CORE_V4130_SCHEMA', (ROOT / 'schemas/sc-core-claim-alignment-agreement-contradiction-intelligence-v1.schema.json').exists())
check('PLATFORM_CORE_V4130_TEST_COVERAGE', (ROOT / 'backend/tests/test_claim_alignment_agreement_contradiction_v4130.py').exists())
check('PLATFORM_CORE_V4130_V412_FORWARD_COMPATIBILITY', '>= (4, 12, 0)' in v412test and '>= (4, 12, 0)' in v412validator)
check('PLATFORM_CORE_V4130_NO_DB_MIGRATION', 'database_migration: Literal["none"]' in service)
print('PLATFORM_CORE_V4130_VALIDATION=PASS')
