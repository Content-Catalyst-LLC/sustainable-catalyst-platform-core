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
service=(ROOT/'backend/app/services/unified_semantic_context_runtime.py').read_text()
readme=(ROOT/'README.md').read_text()
wp=(ROOT/'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text()
wpread=(ROOT/'wordpress-plugin/sustainable-catalyst-platform-core/readme.txt').read_text()
v409=(ROOT/'backend/tests/test_contextual_semantic_evaluation_v4090.py').read_text()

m=re.search(r'version: str = "(\d+)\.(\d+)\.(\d+)"', config)
version=tuple(map(int,m.groups())) if m else (0,0,0)
check('PLATFORM_CORE_V4100_BACKEND_VERSION', version >= (4,10,0))
check('PLATFORM_CORE_V4100_ROUTE_MOUNT', 'unified_semantic_context_runtime.router' in main and 'unified_semantic_context_runtime.public_router' in main)
check('PLATFORM_CORE_V4100_SERVICE_RELEASE', 'CORE_RELEASE = "4.10.0"' in service)
check('PLATFORM_CORE_V4100_CONTRACT', 'sc.core.unified-semantic-contextual-intelligence-runtime.v1' in service)
check('PLATFORM_CORE_V4100_NINE_STAGE_PIPELINE', 'STAGE_ORDER' in service and all(x in service for x in ['context_frame','discourse','reference_identity','temporal_spatial','epistemic','pragmatic','context_graph','multilingual','evaluation']))
check('PLATFORM_CORE_V4100_OBJECT_FOUNDATION', all(x in service for x in ['SemanticRuntimeStageDefinition','SemanticRuntimeArtifactEnvelope','SemanticRuntimeStageResult','RuntimeQualification','UnifiedSemanticRuntimePlan','UnifiedSemanticContextSession','UnifiedSemanticContextSnapshot']))
check('PLATFORM_CORE_V4100_AUTHORITY_BOUNDARY', all(x in service for x in ['runtime_output_is_interpretation_not_truth','core_orchestrates_but_does_not_silently_execute_domain_models','identity_graph_mutation_authorized','evidence_graph_mutation_authorized','knowledge_graph_mutation_authorized']))
check('PLATFORM_CORE_V4100_QUALIFICATION_BOUNDARY', all(x in service for x in ['allow_qualified_continuation','validation_failure_blocks_promotion','ambiguity-preserved','cultural-divergence-preserved','benchmark-non-authoritative']))
check('PLATFORM_CORE_V4100_README', 'v4.10 converges the v4.1-v4.9 stack' in readme or 'v4.10.0 — Unified Semantic & Contextual Intelligence Runtime' in readme)
mwp=re.search(r'\* Version: (\d+)\.(\d+)\.(\d+)', wp)
wp_version=tuple(map(int,mwp.groups())) if mwp else (0,0,0)
check('PLATFORM_CORE_V4100_WORDPRESS_VERSION', wp_version >= (4,10,0) and "SCPC_VERSION" in wp)
mtag=re.search(r'Stable tag: (\d+)\.(\d+)\.(\d+)', wpread)
tag_version=tuple(map(int,mtag.groups())) if mtag else (0,0,0)
check('PLATFORM_CORE_V4100_WORDPRESS_STABLE_TAG', tag_version >= (4,10,0))
check('PLATFORM_CORE_V4100_SCHEMA', (ROOT/'schemas/sc-core-unified-semantic-contextual-intelligence-runtime-v1.schema.json').exists())
check('PLATFORM_CORE_V4100_TEST_COVERAGE', (ROOT/'backend/tests/test_unified_semantic_context_runtime_v4100.py').exists())
check('PLATFORM_CORE_V4100_V49_FORWARD_COMPATIBILITY', '>= (4, 9, 0)' in v409)
check('PLATFORM_CORE_V4100_NO_DB_MIGRATION', 'database_migration: Literal["none"]' in service)
print('PLATFORM_CORE_V4100_VALIDATION=PASS')
