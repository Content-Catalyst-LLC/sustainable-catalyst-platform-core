from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, label: str) -> None:
    if not condition:
        raise SystemExit(f"PLATFORM_CORE_V4030_{label}=FAIL")
    print(f"PLATFORM_CORE_V4030_{label}=PASS")


config = (ROOT / "backend/app/config.py").read_text()
main = (ROOT / "backend/app/main.py").read_text()
service = (ROOT / "backend/app/services/coreference_referential_identity.py").read_text()
router = (ROOT / "backend/app/routers/coreference_referential_identity.py").read_text()
test = (ROOT / "backend/tests/test_coreference_referential_identity_v4030.py").read_text()
v42_test = (ROOT / "backend/tests/test_discourse_structure_rhetorical_semantics_v4020.py").read_text()
readme = (ROOT / "README.md").read_text()
wp = (ROOT / "wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php").read_text()
wp_readme = (ROOT / "wordpress-plugin/sustainable-catalyst-platform-core/readme.txt").read_text()
schema = json.loads((ROOT / "schemas/sc-core-coreference-reference-referential-identity-intelligence-v1.schema.json").read_text())

require('version: str = "4.3.0"' in config, "BACKEND_VERSION")
require("coreference_referential_identity," in main and "coreference_referential_identity.router" in main and "coreference_referential_identity.public_router" in main, "ROUTE_MOUNT")
require('CORE_RELEASE = "4.3.0"' in service, "SERVICE_RELEASE")
require('CONTRACT_VERSION = "sc.core.coreference-reference-referential-identity-intelligence.v1"' in service, "CONTRACT")
require('prefix="/v1/referential-identity"' in router and 'prefix="/public/v1/referential-identity"' in router, "API_SURFACE")
require(all(name in service for name in ["ReferenceExpression", "ReferentAnchor", "ReferentCandidateSet", "CoreferenceLink", "CoreferenceChain", "ReferentialIdentityBinding", "ReferentialInterpretation"]), "OBJECT_FOUNDATION")
require('"core_autonomously_selects_referent": False' in service and '"accepted_resolution_rewrites_v410_source": False' in service, "REFERENCE_BOUNDARY")
require('"coreference_link_establishes_canonical_identity": False' in service and '"referential_identity_binding_merges_entities": False' in service, "IDENTITY_BOUNDARY")
require('**Current release:** v4.3.0' in readme, "README")
require(" * Version: 4.3.0" in wp and "define('SCPC_VERSION', '4.3.0');" in wp, "WORDPRESS_VERSION")
require("Stable tag: 4.3.0" in wp_readme, "WORDPRESS_STABLE_TAG")
require(schema.get("title") == "CoreferenceReferentialIdentityBundle", "SCHEMA")
require("test_v41_unresolved_source_mention_is_preserved" in test and "test_main_app_mounts_v43_routes" in test, "TEST_COVERAGE")
require('assert version >= (4, 2, 0)' in v42_test, "V42_FORWARD_COMPATIBILITY")
print("PLATFORM_CORE_V4030_VALIDATION=PASS")
