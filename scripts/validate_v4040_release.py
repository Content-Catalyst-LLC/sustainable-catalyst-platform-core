from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, label: str) -> None:
    if not condition:
        raise SystemExit(f"PLATFORM_CORE_V4040_{label}=FAIL")
    print(f"PLATFORM_CORE_V4040_{label}=PASS")


config = (ROOT / "backend/app/config.py").read_text()
main = (ROOT / "backend/app/main.py").read_text()
service = (ROOT / "backend/app/services/temporal_spatial_language_grounding.py").read_text()
router = (ROOT / "backend/app/routers/temporal_spatial_language_grounding.py").read_text()
test = (ROOT / "backend/tests/test_temporal_spatial_language_grounding_v4040.py").read_text()
v43_test = (ROOT / "backend/tests/test_coreference_referential_identity_v4030.py").read_text()
readme = (ROOT / "README.md").read_text()
wp = (ROOT / "wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php").read_text()
wp_readme = (ROOT / "wordpress-plugin/sustainable-catalyst-platform-core/readme.txt").read_text()
schema = json.loads((ROOT / "schemas/sc-core-temporal-spatial-language-grounding-v1.schema.json").read_text())

require('version: str = "4.4.0"' in config, "BACKEND_VERSION")
require("temporal_spatial_language_grounding," in main and "temporal_spatial_language_grounding.router" in main and "temporal_spatial_language_grounding.public_router" in main, "ROUTE_MOUNT")
require('CORE_RELEASE = "4.4.0"' in service, "SERVICE_RELEASE")
require('CONTRACT_VERSION = "sc.core.temporal-spatial-language-grounding.v1"' in service, "CONTRACT")
require('prefix="/v1/language-grounding"' in router and 'prefix="/public/v1/language-grounding"' in router, "API_SURFACE")
require(all(name in service for name in ["TemporalExpression", "SpatialExpression", "TemporalAnchor", "SpatialAnchor", "GroundingCandidateSet", "TemporalGrounding", "SpatialGrounding", "TemporalRelationGrounding"]), "OBJECT_FOUNDATION")
require('"core_autonomously_geocodes_named_place": False' in service and '"temporal_relation_establishes_real_world_event_order": False' in service, "GROUNDING_BOUNDARY")
require('"relative_time_flattens_derivation_history": False' in service and '"accepted_grounding_rewrites_v430_predecessor": False' in service, "PROVENANCE_BOUNDARY")
require('**Current release:** v4.4.0' in readme, "README")
require(" * Version: 4.4.0" in wp and "define('SCPC_VERSION', '4.4.0');" in wp, "WORDPRESS_VERSION")
require("Stable tag: 4.4.0" in wp_readme, "WORDPRESS_STABLE_TAG")
require(schema.get("title") == "TemporalSpatialLanguageGroundingBundle", "SCHEMA")
require("test_relative_year_preserves_base_expression" in test and "test_main_app_mounts_v44_routes" in test, "TEST_COVERAGE")
require('assert version >= (4, 3, 0)' in v43_test, "V43_FORWARD_COMPATIBILITY")
print("PLATFORM_CORE_V4040_VALIDATION=PASS")
