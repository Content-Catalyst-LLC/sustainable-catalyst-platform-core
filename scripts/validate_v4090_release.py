#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
checks=[]

def check(label, cond):
    if not cond:
        raise SystemExit(f"{label}=FAIL")
    print(f"{label}=PASS")

config=(ROOT/'backend/app/config.py').read_text()
main=(ROOT/'backend/app/main.py').read_text()
service=(ROOT/'backend/app/services/contextual_semantic_evaluation.py').read_text()
readme=(ROOT/'README.md').read_text()
wp=(ROOT/'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text()
wpread=(ROOT/'wordpress-plugin/sustainable-catalyst-platform-core/readme.txt').read_text()

def has(p,s): return p in s
check('PLATFORM_CORE_V4090_BACKEND_VERSION', has('version: str = "4.9.0"', config))
check('PLATFORM_CORE_V4090_ROUTE_MOUNT', 'contextual_semantic_evaluation.router' in main and 'contextual_semantic_evaluation.public_router' in main)
check('PLATFORM_CORE_V4090_SERVICE_RELEASE', 'CORE_RELEASE = "4.9.0"' in service)
check('PLATFORM_CORE_V4090_CONTRACT', 'sc.core.contextual-semantic-evaluation-benchmark-framework.v1' in service)
check('PLATFORM_CORE_V4090_OBJECT_FOUNDATION', all(x in service for x in ['ContextualSemanticBenchmarkCase','BenchmarkGoldAnnotation','ContextualSemanticEvaluationRun','MetricDefinition','MetricResult','BenchmarkSnapshot']))
check('PLATFORM_CORE_V4090_EVALUATION_BOUNDARY', all(x in service for x in ['benchmark_pass_does_not_establish_claim_truth','benchmark_score_does_not_establish_model_safety','benchmark_gold_is_reviewed_target_not_world_truth']))
check('PLATFORM_CORE_V4090_AMBIGUITY_BOUNDARY', 'unresolved_ambiguity_may_be_correct_behavior' in service and 'ambiguity-preservation' in service)
check('PLATFORM_CORE_V4090_README', 'v4.9.0 — Contextual Semantic Evaluation & Benchmark Framework' in readme)
check('PLATFORM_CORE_V4090_WORDPRESS_VERSION', 'Version: 4.9.0' in wp and "SCPC_VERSION', '4.9.0" in wp)
check('PLATFORM_CORE_V4090_WORDPRESS_STABLE_TAG', 'Stable tag: 4.9.0' in wpread)
check('PLATFORM_CORE_V4090_SCHEMA', (ROOT/'schemas/sc-core-contextual-semantic-evaluation-benchmark-framework-v1.schema.json').exists())
check('PLATFORM_CORE_V4090_TEST_COVERAGE', (ROOT/'backend/tests/test_contextual_semantic_evaluation_v4090.py').exists())
check('PLATFORM_CORE_V4090_V48_FORWARD_COMPATIBILITY', 'Settings().version' in (ROOT/'backend/tests/test_multilingual_context_semantic_alignment_v4080.py').read_text())
print('PLATFORM_CORE_V4090_VALIDATION=PASS')
