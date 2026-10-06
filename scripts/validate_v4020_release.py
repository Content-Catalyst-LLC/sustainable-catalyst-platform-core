from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, label: str) -> None:
    if not condition:
        raise SystemExit(f"PLATFORM_CORE_V4020_{label}=FAIL")
    print(f"PLATFORM_CORE_V4020_{label}=PASS")


config = (ROOT / "backend/app/config.py").read_text()
main = (ROOT / "backend/app/main.py").read_text()
service = (ROOT / "backend/app/services/discourse_rhetorical_semantics.py").read_text()
router = (ROOT / "backend/app/routers/discourse_rhetorical_semantics.py").read_text()
test = (ROOT / "backend/tests/test_discourse_structure_rhetorical_semantics_v4020.py").read_text()
readme = (ROOT / "README.md").read_text()
wp = (ROOT / "wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php").read_text()
wp_readme = (ROOT / "wordpress-plugin/sustainable-catalyst-platform-core/readme.txt").read_text()
schema = json.loads((ROOT / "schemas/sc-core-discourse-structure-rhetorical-semantics-v1.schema.json").read_text())

require('version: str = "4.2.0"' in config, "BACKEND_VERSION")
require("discourse_rhetorical_semantics," in main and "discourse_rhetorical_semantics.router" in main and "discourse_rhetorical_semantics.public_router" in main, "ROUTE_MOUNT")
require('CORE_RELEASE = "4.2.0"' in service, "SERVICE_RELEASE")
require('CONTRACT_VERSION = "sc.core.discourse-structure-rhetorical-semantics.v1"' in service, "CONTRACT")
require('prefix="/v1/discourse-semantics"' in router and 'prefix="/public/v1/discourse-semantics"' in router, "API_SURFACE")
require("DiscourseSegment" in service and "RhetoricalRelation" in service and "ArgumentUnit" in service and "DiscourseInterpretation" in service, "OBJECT_FOUNDATION")
require('"core_autonomously_infers_discourse_relations": False' in service and '"core_resolves_coreference": False' in service, "SCOPE_BOUNDARY")
require('"rhetorical_cause_establishes_real_world_causality": False' in service and '"rhetorical_evidence_establishes_evidence_strength": False' in service, "EPISTEMIC_BOUNDARY")
require('**Current release:** v4.2.0' in readme, "README")
require(" * Version: 4.2.0" in wp and "define('SCPC_VERSION', '4.2.0');" in wp, "WORDPRESS_VERSION")
require("Stable tag: 4.2.0" in wp_readme, "WORDPRESS_STABLE_TAG")
require(schema.get("title") == "DiscourseStructureRhetoricalSemanticsBundle", "SCHEMA")
require("test_v42_preserves_v41_unresolved_reference" in test and "test_main_app_mounts_v42_routes" in test, "TEST_COVERAGE")
print("PLATFORM_CORE_V4020_VALIDATION=PASS")
