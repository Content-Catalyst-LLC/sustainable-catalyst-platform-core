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
service = (ROOT / 'backend/app/services/context_retrieval_relevance.py').read_text()
router = (ROOT / 'backend/app/routers/context_retrieval_relevance.py').read_text()
readme = (ROOT / 'README.md').read_text()
wp = (ROOT / 'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text()
wpread = (ROOT / 'wordpress-plugin/sustainable-catalyst-platform-core/readme.txt').read_text()
v411test = (ROOT / 'backend/tests/test_contextual_memory_semantic_state_v4110.py').read_text()
v411validator = (ROOT / 'scripts/validate_v4110_release.py').read_text()

m = re.search(r'version: str = \"(\d+)\.(\d+)\.(\d+)\"', config)
check('PLATFORM_CORE_V4120_BACKEND_VERSION', bool(m) and tuple(map(int, m.groups())) >= (4, 12, 0))
check('PLATFORM_CORE_V4120_ROUTE_MOUNT', 'context_retrieval_relevance.router' in main and 'context_retrieval_relevance.public_router' in main)
check('PLATFORM_CORE_V4120_SERVICE_RELEASE', 'CORE_RELEASE = "4.12.0"' in service)
check('PLATFORM_CORE_V4120_CONTRACT', 'sc.core.context-retrieval-relevance-intelligence.v1' in service)
check('PLATFORM_CORE_V4120_API_SURFACE', '/v1/context-retrieval' in router and '/public/v1/context-retrieval' in router)
check('PLATFORM_CORE_V4120_QUERY_FOUNDATION', all(x in service for x in ['ContextRetrievalQuery', 'RetrievalQueryKind', 'RetrievalMethodKind']))
check('PLATFORM_CORE_V4120_RELEVANCE_FOUNDATION', all(x in service for x in ['RelevanceSignal', 'RetrievalCandidate', 'RankedRetrievalResult', 'ContextRetrievalResultSet']))
check('PLATFORM_CORE_V4120_PROVENANCE_SNAPSHOT', all(x in service for x in ['RetrievalProvenanceRecord', 'ContextRetrievalSnapshot', 'deterministic_retrieval_fingerprint_sha256']))
check('PLATFORM_CORE_V4120_EXPLAINABILITY_BOUNDARY', all(x in service for x in ['ranking_must_be_explainable', 'candidate_generation_and_ranking_are_distinct', 'qualifications_must_travel_with_results', 'unresolved_context_must_not_be_silently_dropped']))
check('PLATFORM_CORE_V4120_EPISTEMIC_BOUNDARY', all(x in service for x in ['retrieval_rank_establishes_truth', 'relevance_score_is_evidence_weight', 'semantic_similarity_establishes_equivalence', 'scope_proximity_establishes_authority', 'provenance_completeness_establishes_credibility']))
check('PLATFORM_CORE_V4120_GRAPH_BOUNDARY', all(x in service for x in ['context_graph_mutation_authorized', 'identity_graph_mutation_authorized', 'evidence_graph_mutation_authorized', 'knowledge_graph_mutation_authorized']))
check('PLATFORM_CORE_V4120_README', 'v4.12.0 — Context Retrieval & Relevance Intelligence' in readme)
wm = re.search(r'Version: (\d+)\.(\d+)\.(\d+)', wp)
wc = re.search(r"SCPC_VERSION', '(\d+)\.(\d+)\.(\d+)", wp)
check('PLATFORM_CORE_V4120_WORDPRESS_VERSION', bool(wm) and bool(wc) and tuple(map(int, wm.groups())) >= (4, 12, 0) and tuple(map(int, wc.groups())) >= (4, 12, 0))
ws = re.search(r'Stable tag: (\d+)\.(\d+)\.(\d+)', wpread)
check('PLATFORM_CORE_V4120_WORDPRESS_STABLE_TAG', bool(ws) and tuple(map(int, ws.groups())) >= (4, 12, 0))
check('PLATFORM_CORE_V4120_SCHEMA', (ROOT / 'schemas/sc-core-context-retrieval-relevance-intelligence-v1.schema.json').exists())
check('PLATFORM_CORE_V4120_TEST_COVERAGE', (ROOT / 'backend/tests/test_context_retrieval_relevance_v4120.py').exists())
check('PLATFORM_CORE_V4120_V411_FORWARD_COMPATIBILITY', '>= (4, 11, 0)' in v411test and '>= (4, 11, 0)' in v411validator)
check('PLATFORM_CORE_V4120_NO_DB_MIGRATION', 'database_migration: Literal["none"]' in service)
print('PLATFORM_CORE_V4120_VALIDATION=PASS')
