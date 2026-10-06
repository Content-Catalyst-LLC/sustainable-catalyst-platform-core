from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, label: str) -> None:
    if not condition:
        raise SystemExit(f"PLATFORM_CORE_V4010_{label}=FAIL")
    print(f"PLATFORM_CORE_V4010_{label}=PASS")


config = (ROOT / "backend/app/config.py").read_text()
main = (ROOT / "backend/app/main.py").read_text()
service = (ROOT / "backend/app/services/context_semantic_frame.py").read_text()
router = (ROOT / "backend/app/routers/context_semantic_frame.py").read_text()
test = (ROOT / "backend/tests/test_context_object_semantic_frame_foundation_v4010.py").read_text()
readme = (ROOT / "README.md").read_text()
wp = (ROOT / "wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php").read_text()
wp_readme = (ROOT / "wordpress-plugin/sustainable-catalyst-platform-core/readme.txt").read_text()
schema = json.loads((ROOT / "schemas/sc-core-context-object-semantic-frame-foundation-v1.schema.json").read_text())

require('version: str = "4.1.0"' in config, "BACKEND_VERSION")
require("context_semantic_frame," in main and "context_semantic_frame.router" in main and "context_semantic_frame.public_router" in main, "ROUTE_MOUNT")
require('CORE_RELEASE = "4.1.0"' in service, "SERVICE_RELEASE")
require('CONTRACT_VERSION = "sc.core.context-object-semantic-frame-foundation.v1"' in service, "CONTRACT")
require('prefix="/v1/context-semantics"' in router and 'prefix="/public/v1/context-semantics"' in router, "API_SURFACE")
require("ContextObject" in service and "SemanticFrame" in service and "SemanticInterpretation" in service, "OBJECT_FOUNDATION")
require('"core_resolves_coreference": False' in service and '"core_infers_discourse_relations": False' in service, "SCOPE_BOUNDARY")
require('"semantic_frame_establishes_source_truth": False' in service and '"evidence_graph_mutation_performed": False' in service, "EPISTEMIC_BOUNDARY")
require('**Current release:** v4.1.0' in readme, "README")
require(" * Version: 4.1.0" in wp and "define('SCPC_VERSION', '4.1.0');" in wp, "WORDPRESS_VERSION")
require("Stable tag: 4.1.0" in wp_readme, "WORDPRESS_STABLE_TAG")
require(schema.get("title") == "ContextObjectSemanticFrameBundle", "SCHEMA")
require("test_unresolved_reference_is_preserved" in test and "test_main_app_mounts_v41_routes" in test, "TEST_COVERAGE")
print("PLATFORM_CORE_V4010_VALIDATION=PASS")
