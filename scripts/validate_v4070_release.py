from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, label: str) -> None:
    if not condition:
        raise SystemExit(f"PLATFORM_CORE_V4070_{label}=FAIL")
    print(f"PLATFORM_CORE_V4070_{label}=PASS")


config = (ROOT / "backend/app/config.py").read_text()
main = (ROOT / "backend/app/main.py").read_text()
service = (ROOT / "backend/app/services/cross_document_context_graph.py").read_text()
router = (ROOT / "backend/app/routers/cross_document_context_graph.py").read_text()
test = (ROOT / "backend/tests/test_cross_document_context_graph_v4070.py").read_text()
v46_test = (ROOT / "backend/tests/test_pragmatic_meaning_speech_act_intent_v4060.py").read_text()
readme = (ROOT / "README.md").read_text()
wp = (ROOT / "wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php").read_text()
wp_readme = (ROOT / "wordpress-plugin/sustainable-catalyst-platform-core/readme.txt").read_text()
schema = json.loads((ROOT / "schemas/sc-core-cross-document-context-graph-v1.schema.json").read_text())

definition_names = set(schema.get("$defs", {}))

require('version: str = "4.7.0"' in config, "BACKEND_VERSION")
require("cross_document_context_graph," in main and "cross_document_context_graph.router" in main and "cross_document_context_graph.public_router" in main, "ROUTE_MOUNT")
require('CORE_RELEASE = "4.7.0"' in service, "SERVICE_RELEASE")
require('CONTRACT_VERSION = "sc.core.cross-document-context-graph.v1"' in service, "CONTRACT")
require('prefix="/v1/context-graph"' in router and 'prefix="/public/v1/context-graph"' in router, "API_SURFACE")
require(all(name in service for name in ["ContextDocumentBinding", "ContextGraphNode", "ContextGraphEdge", "CrossDocumentContextThread", "ContextGraphInterpretation", "CrossDocumentContextGraphSnapshot"]), "OBJECT_FOUNDATION")
require('"context_graph_establishes_world_truth": False' in service and '"cross_document_link_establishes_canonical_identity": False' in service, "EPISTEMIC_BOUNDARY")
require('"identity_graph_mutation_performed": False' in service and '"evidence_graph_mutation_performed": False' in service and '"knowledge_graph_mutation_performed": False' in service, "GRAPH_MUTATION_BOUNDARY")
require('**Current release:** v4.7.0 — Cross-Document Context Graph' in readme, "README")
require(" * Version: 4.7.0" in wp and "define('SCPC_VERSION', '4.7.0');" in wp, "WORDPRESS_VERSION")
require("Stable tag: 4.7.0" in wp_readme, "WORDPRESS_STABLE_TAG")
require(schema.get("title") == "CrossDocumentContextGraphBundle", "SCHEMA")
require({"ContextDocumentBinding", "ContextGraphNode", "ContextGraphEdge", "CrossDocumentContextThread", "ContextGraphInterpretation", "CrossDocumentContextGraphSnapshot"}.issubset(definition_names), "SCHEMA_OBJECTS")
require("test_actor_continuity_is_proposed_not_identity_merge" in test and "test_topic_continuity_is_proposed_not_object_equivalence" in test and "test_main_app_mounts_v47_routes" in test, "TEST_COVERAGE")
require('tuple(map(int, Settings().version.split("."))) >= (4, 6, 0)' in v46_test, "V46_FORWARD_COMPATIBILITY")
print("PLATFORM_CORE_V4070_VALIDATION=PASS")
