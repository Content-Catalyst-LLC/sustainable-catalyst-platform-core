#!/usr/bin/env python3
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
def check(label,cond):
    if not cond: raise SystemExit(f"{label}=FAIL")
    print(f"{label}=PASS")
config=(ROOT/'backend/app/config.py').read_text(); main=(ROOT/'backend/app/main.py').read_text(); service=(ROOT/'backend/app/services/semantic_synthesis_research_answer.py').read_text(); router=(ROOT/'backend/app/routers/semantic_synthesis_research_answer.py').read_text(); readme=(ROOT/'README.md').read_text(); wp=(ROOT/'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text(); wpread=(ROOT/'wordpress-plugin/sustainable-catalyst-platform-core/readme.txt').read_text(); v418v=(ROOT/'scripts/validate_v4180_release.py').read_text()
m=re.search(r'version: str = "(\d+)\.(\d+)\.(\d+)"',config); av=tuple(map(int,m.groups())) if m else (0,0,0)
check('PLATFORM_CORE_V4190_BACKEND_VERSION',av >= (4,19,0))
check('PLATFORM_CORE_V4190_ROUTE_MOUNT','semantic_synthesis_research_answer.router' in main and 'semantic_synthesis_research_answer.public_router' in main)
check('PLATFORM_CORE_V4190_SERVICE_RELEASE','CORE_RELEASE = "4.19.0"' in service)
check('PLATFORM_CORE_V4190_CONTRACT','sc.core.semantic-synthesis-research-answer-object.v1' in service)
check('PLATFORM_CORE_V4190_API_SURFACE','/v1/research-answers' in router and '/public/v1/research-answers' in router)
check('PLATFORM_CORE_V4190_SYNTHESIS_CLAIM_FOUNDATION',all(x in service for x in ['SynthesisClaim','SynthesisClaimRole','claim_is_not_truth_promotion']))
check('PLATFORM_CORE_V4190_RESEARCH_ANSWER_FOUNDATION',all(x in service for x in ['ResearchAnswerObject','AnswerDisposition','answer_is_not_truth_verdict','confidence_is_not_probability']))
check('PLATFORM_CORE_V4190_PROVENANCE_SNAPSHOT',all(x in service for x in ['ResearchAnswerProvenanceRecord','ResearchAnswerSnapshot','deterministic_synthesis_fingerprint_sha256']))
check('PLATFORM_CORE_V4190_EPISTEMIC_BOUNDARY',all(x in service for x in ['answer_disposition_establishes_truth','answer_confidence_establishes_probability','majority_source_count_establishes_truth','rejected_explanation_establishes_opposite_truth']))
check('PLATFORM_CORE_V4190_MUTATION_BOUNDARY',all(x in service for x in ['automatic_evidence_promotion_authorized','automatic_hypothesis_selection_authorized','automatic_context_graph_mutation_authorized','automatic_evidence_graph_mutation_authorized','automatic_knowledge_graph_mutation_authorized','automatic_identity_graph_mutation_authorized']))
check('PLATFORM_CORE_V4190_README','v4.19.0 — Semantic Synthesis & Research Answer Object' in readme)
wm=re.search(r'Version: (\d+)\.(\d+)\.(\d+)',wp); wv=tuple(map(int,wm.groups())) if wm else (0,0,0); check('PLATFORM_CORE_V4190_WORDPRESS_VERSION',wv >= (4,19,0))
tm=re.search(r'Stable tag: (\d+)\.(\d+)\.(\d+)',wpread); tv=tuple(map(int,tm.groups())) if tm else (0,0,0); check('PLATFORM_CORE_V4190_WORDPRESS_STABLE_TAG',tv >= (4,19,0))
check('PLATFORM_CORE_V4190_SCHEMA',(ROOT/'schemas/sc-core-semantic-synthesis-research-answer-object-v1.schema.json').exists())
check('PLATFORM_CORE_V4190_TEST_COVERAGE',(ROOT/'backend/tests/test_semantic_synthesis_research_answer_v4190.py').exists())
check('PLATFORM_CORE_V4190_V418_FORWARD_COMPATIBILITY','_app_version >= (4,18,0)' in v418v and '_wp_version >= (4,18,0)' in v418v and '_wp_tag >= (4,18,0)' in v418v)
check('PLATFORM_CORE_V4190_NO_DB_MIGRATION','database_migration: Literal["none"]' in service)
print('PLATFORM_CORE_V4190_VALIDATION=PASS')
