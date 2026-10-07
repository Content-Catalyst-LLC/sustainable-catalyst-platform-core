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
service = (ROOT / 'backend/app/services/contextual_memory_semantic_state.py').read_text()
router = (ROOT / 'backend/app/routers/contextual_memory_semantic_state.py').read_text()
readme = (ROOT / 'README.md').read_text()
wp = (ROOT / 'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text()
wpread = (ROOT / 'wordpress-plugin/sustainable-catalyst-platform-core/readme.txt').read_text()
v410test = (ROOT / 'backend/tests/test_unified_semantic_context_runtime_v4100.py').read_text()

check('PLATFORM_CORE_V4110_BACKEND_VERSION', 'version: str = "4.11.0"' in config)
check('PLATFORM_CORE_V4110_ROUTE_MOUNT', 'contextual_memory_semantic_state.router' in main and 'contextual_memory_semantic_state.public_router' in main)
check('PLATFORM_CORE_V4110_SERVICE_RELEASE', 'CORE_RELEASE = "4.11.0"' in service)
check('PLATFORM_CORE_V4110_CONTRACT', 'sc.core.contextual-memory-semantic-state-foundation.v1' in service)
check('PLATFORM_CORE_V4110_API_SURFACE', '/v1/context-memory' in router and '/public/v1/context-memory' in router)
check('PLATFORM_CORE_V4110_SCOPE_FOUNDATION', all(x in service for x in ['document = "document"', 'runtime_session = "runtime-session"', 'investigation = "investigation"', 'research_project = "research-project"']))
check('PLATFORM_CORE_V4110_OBJECT_FOUNDATION', all(x in service for x in ['ContextualMemoryScope', 'SemanticMemoryEntry', 'SemanticStateRevision', 'MemoryCarryForward', 'ContextualMemoryLink', 'ContextualMemoryCheckpoint', 'ContextualMemorySnapshot']))
check('PLATFORM_CORE_V4110_REVISION_BOUNDARY', all(x in service for x in ['revisions_are_immutable', 'supersession_preserves_prior_revisions', 'stable_identity_across_revisions', 'revision_does_not_rewrite_source_semantics']))
check('PLATFORM_CORE_V4110_EPISTEMIC_BOUNDARY', all(x in service for x in ['memory_persistence_establishes_truth', 'memory_repetition_increases_truth', 'carried_forward_state_establishes_canonical_identity', 'storage_backend_is_not_semantic_authority']))
check('PLATFORM_CORE_V4110_GRAPH_BOUNDARY', all(x in service for x in ['context_graph_mutation_authorized', 'identity_graph_mutation_authorized', 'evidence_graph_mutation_authorized', 'knowledge_graph_mutation_authorized']))
check('PLATFORM_CORE_V4110_README', 'v4.11.0 — Contextual Memory & Semantic State Foundation' in readme)
check('PLATFORM_CORE_V4110_WORDPRESS_VERSION', 'Version: 4.11.0' in wp and "SCPC_VERSION', '4.11.0" in wp)
check('PLATFORM_CORE_V4110_WORDPRESS_STABLE_TAG', 'Stable tag: 4.11.0' in wpread)
check('PLATFORM_CORE_V4110_SCHEMA', (ROOT / 'schemas/sc-core-contextual-memory-semantic-state-foundation-v1.schema.json').exists())
check('PLATFORM_CORE_V4110_TEST_COVERAGE', (ROOT / 'backend/tests/test_contextual_memory_semantic_state_v4110.py').exists())
check('PLATFORM_CORE_V4110_V410_FORWARD_COMPATIBILITY', '>= (4, 10, 0)' in v410test)
check('PLATFORM_CORE_V4110_NO_DB_MIGRATION', 'database_migration: Literal["none"]' in service)
print('PLATFORM_CORE_V4110_VALIDATION=PASS')
