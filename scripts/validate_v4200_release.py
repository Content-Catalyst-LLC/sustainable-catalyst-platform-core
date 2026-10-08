#!/usr/bin/env python3
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
def check(label,cond):
    if not cond: raise SystemExit(f"{label}=FAIL")
    print(f"{label}=PASS")
config=(ROOT/'backend/app/config.py').read_text(); main=(ROOT/'backend/app/main.py').read_text(); service=(ROOT/'backend/app/services/unified_contextual_reasoning_runtime.py').read_text(); router=(ROOT/'backend/app/routers/unified_contextual_reasoning_runtime.py').read_text(); readme=(ROOT/'README.md').read_text(); wp=(ROOT/'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text(); wpread=(ROOT/'wordpress-plugin/sustainable-catalyst-platform-core/readme.txt').read_text(); v419v=(ROOT/'scripts/validate_v4190_release.py').read_text()
m=re.search(r'version: str = "(\d+)\.(\d+)\.(\d+)"',config); av=tuple(map(int,m.groups())) if m else (0,0,0)
check('PLATFORM_CORE_V4200_BACKEND_VERSION',av >= (4,20,0))
check('PLATFORM_CORE_V4200_ROUTE_MOUNT','unified_contextual_reasoning_runtime.router' in main and 'unified_contextual_reasoning_runtime.public_router' in main)
check('PLATFORM_CORE_V4200_SERVICE_RELEASE','CORE_RELEASE = "4.20.0"' in service)
check('PLATFORM_CORE_V4200_CONTRACT','sc.core.unified-contextual-reasoning-runtime.v1' in service)
check('PLATFORM_CORE_V4200_API_SURFACE','/v1/contextual-reasoning' in router and '/public/v1/contextual-reasoning' in router)
check('PLATFORM_CORE_V4200_STAGE_FOUNDATION',all(x in service for x in ['ReasoningStageKind','ReasoningStageRecord','stage_order_is_governed','qualifications_must_propagate_forward']))
check('PLATFORM_CORE_V4200_TRACE_FOUNDATION',all(x in service for x in ['UnifiedReasoningTrace','trace_is_audit_record_not_truth_verdict','final_answer_remains_governed_synthesis']))
check('PLATFORM_CORE_V4200_PROVENANCE_SNAPSHOT',all(x in service for x in ['UnifiedReasoningRuntimeProvenance','UnifiedReasoningRuntimeSnapshot','deterministic_runtime_fingerprint_sha256']))
check('PLATFORM_CORE_V4200_EPISTEMIC_BOUNDARY',all(x in service for x in ['stage_completion_establishes_truth','runtime_completion_establishes_truth','runtime_confidence_is_probability','synthesis_answer_is_evidence_record']))
check('PLATFORM_CORE_V4200_MUTATION_BOUNDARY',all(x in service for x in ['automatic_evidence_promotion_authorized','automatic_hypothesis_selection_authorized','automatic_canonical_identity_merge_authorized','automatic_context_graph_mutation_authorized','automatic_evidence_graph_mutation_authorized','automatic_knowledge_graph_mutation_authorized','automatic_identity_graph_mutation_authorized']))
check('PLATFORM_CORE_V4200_MILESTONE','contextual_reasoning_arc_complete' in service and 'recommended_core_feature_expansion_pause' in service)
check('PLATFORM_CORE_V4200_README','v4.20.0 — Unified Contextual Reasoning Runtime' in readme)
wm=re.search(r'Version: (\d+)\.(\d+)\.(\d+)',wp); wv=tuple(map(int,wm.groups())) if wm else (0,0,0); check('PLATFORM_CORE_V4200_WORDPRESS_VERSION',wv >= (4,20,0))
tm=re.search(r'Stable tag: (\d+)\.(\d+)\.(\d+)',wpread); tv=tuple(map(int,tm.groups())) if tm else (0,0,0); check('PLATFORM_CORE_V4200_WORDPRESS_STABLE_TAG',tv >= (4,20,0))
check('PLATFORM_CORE_V4200_SCHEMA',(ROOT/'schemas/sc-core-unified-contextual-reasoning-runtime-v1.schema.json').exists())
check('PLATFORM_CORE_V4200_TEST_COVERAGE',(ROOT/'backend/tests/test_unified_contextual_reasoning_runtime_v4200.py').exists())
check('PLATFORM_CORE_V4200_V419_FORWARD_COMPATIBILITY','av >= (4,19,0)' in v419v and 'wv >= (4,19,0)' in v419v and 'tv >= (4,19,0)' in v419v)
check('PLATFORM_CORE_V4200_NO_DB_MIGRATION','database_migration: Literal["none"]' in service)
print('PLATFORM_CORE_V4200_VALIDATION=PASS')
