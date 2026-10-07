from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, label: str) -> None:
    if not condition:
        raise SystemExit(f"PLATFORM_CORE_V4080_{label}=FAIL")
    print(f"PLATFORM_CORE_V4080_{label}=PASS")


config = (ROOT / "backend/app/config.py").read_text()
main = (ROOT / "backend/app/main.py").read_text()
service = (ROOT / "backend/app/services/multilingual_context_semantic_alignment.py").read_text()
router = (ROOT / "backend/app/routers/multilingual_context_semantic_alignment.py").read_text()
test = (ROOT / "backend/tests/test_multilingual_context_semantic_alignment_v4080.py").read_text()
v47_test = (ROOT / "backend/tests/test_cross_document_context_graph_v4070.py").read_text()
readme = (ROOT / "README.md").read_text()
wp = (ROOT / "wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php").read_text()
wp_readme = (ROOT / "wordpress-plugin/sustainable-catalyst-platform-core/readme.txt").read_text()
schema = json.loads((ROOT / "schemas/sc-core-multilingual-context-semantic-alignment-v1.schema.json").read_text())
definition_names = set(schema.get("$defs", {}))

require('version: str = "4.8.0"' in config, "BACKEND_VERSION")
require("multilingual_context_semantic_alignment," in main and "multilingual_context_semantic_alignment.router" in main and "multilingual_context_semantic_alignment.public_router" in main, "ROUTE_MOUNT")
require('CORE_RELEASE = "4.8.0"' in service, "SERVICE_RELEASE")
require('CONTRACT_VERSION = "sc.core.multilingual-context-semantic-alignment.v1"' in service, "CONTRACT")
require('prefix="/v1/multilingual-context"' in router and 'prefix="/public/v1/multilingual-context"' in router, "API_SURFACE")
require(all(name in service for name in ["ContextLanguageRepresentation", "ContextSemanticUnit", "MultilingualContextAlignment", "SemanticDivergenceRecord", "ContextGraphProjectionBinding", "MultilingualContextInterpretation", "MultilingualContextSnapshot"]), "OBJECT_FOUNDATION")
require('"translation_replaces_original_source": False' in service and '"semantic_similarity_establishes_equivalence": False' in service and '"culturally_conditioned_alignment_establishes_universal_equivalence": False' in service, "SEMANTIC_BOUNDARY")
require('"multilingual_projection_mutates_v470_context_graph": False' in service and '"identity_graph_mutation_performed": False' in service and '"evidence_graph_mutation_performed": False' in service and '"knowledge_graph_mutation_performed": False' in service, "GRAPH_MUTATION_BOUNDARY")
require('**Current release:** v4.8.0 — Multilingual Context & Semantic Alignment' in readme, "README")
require(" * Version: 4.8.0" in wp and "define('SCPC_VERSION', '4.8.0');" in wp, "WORDPRESS_VERSION")
require("Stable tag: 4.8.0" in wp_readme, "WORDPRESS_STABLE_TAG")
require(schema.get("title") == "MultilingualContextSemanticAlignmentBundle", "SCHEMA")
require({"ContextLanguageRepresentation", "ContextSemanticUnit", "MultilingualContextAlignment", "SemanticDivergenceRecord", "ContextGraphProjectionBinding", "MultilingualContextInterpretation", "MultilingualContextSnapshot"}.issubset(definition_names), "SCHEMA_OBJECTS")
require("test_governance_alignment_is_culturally_conditioned_not_exact_equivalence" in test and "test_context_graph_projection_is_candidate_and_non_mutating" in test and "test_main_app_mounts_v48_routes" in test, "TEST_COVERAGE")
require('tuple(map(int, Settings().version.split("."))) >= (4, 7, 0)' in v47_test, "V47_FORWARD_COMPATIBILITY")
print("PLATFORM_CORE_V4080_VALIDATION=PASS")
