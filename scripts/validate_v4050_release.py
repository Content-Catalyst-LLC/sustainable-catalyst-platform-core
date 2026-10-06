from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, label: str) -> None:
    if not condition:
        raise SystemExit(f"PLATFORM_CORE_V4050_{label}=FAIL")
    print(f"PLATFORM_CORE_V4050_{label}=PASS")


config = (ROOT / "backend/app/config.py").read_text()
main = (ROOT / "backend/app/main.py").read_text()
service = (ROOT / "backend/app/services/epistemic_modal_negation_certainty.py").read_text()
router = (ROOT / "backend/app/routers/epistemic_modal_negation_certainty.py").read_text()
test = (ROOT / "backend/tests/test_epistemic_modal_negation_certainty_v4050.py").read_text()
v44_test = (ROOT / "backend/tests/test_temporal_spatial_language_grounding_v4040.py").read_text()
readme = (ROOT / "README.md").read_text()
wp = (ROOT / "wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php").read_text()
wp_readme = (ROOT / "wordpress-plugin/sustainable-catalyst-platform-core/readme.txt").read_text()
schema = json.loads((ROOT / "schemas/sc-core-epistemic-modal-negation-certainty-semantics-v1.schema.json").read_text())

require('version: str = "4.5.0"' in config, "BACKEND_VERSION")
require("epistemic_modal_negation_certainty," in main and "epistemic_modal_negation_certainty.router" in main and "epistemic_modal_negation_certainty.public_router" in main, "ROUTE_MOUNT")
require('CORE_RELEASE = "4.5.0"' in service, "SERVICE_RELEASE")
require('CONTRACT_VERSION = "sc.core.epistemic-modal-negation-certainty-semantics.v1"' in service, "CONTRACT")
require('prefix="/v1/epistemic-semantics"' in router and 'prefix="/public/v1/epistemic-semantics"' in router, "API_SURFACE")
require(all(name in service for name in ["Proposition", "Attribution", "EpistemicCue", "NegationScope", "ModalScope", "ConditionalScope", "EpistemicAssessment"]), "OBJECT_FOUNDATION")
require('"reported_claim_establishes_platform_truth": False' in service and '"linguistic_confidence_is_claim_probability": False' in service, "EPISTEMIC_BOUNDARY")
require('"surface_source_establishes_canonical_actor_identity": False' in service and '"accepted_epistemic_analysis_rewrites_v440_predecessor": False' in service, "IDENTITY_BOUNDARY")
require('**Current release:** v4.5.0 — Epistemic, Modal, Negation & Certainty Semantics' in readme, "README")
require(" * Version: 4.5.0" in wp and "define('SCPC_VERSION', '4.5.0');" in wp, "WORDPRESS_VERSION")
require("Stable tag: 4.5.0" in wp_readme, "WORDPRESS_STABLE_TAG")
require(schema.get("title") == "EpistemicModalNegationCertaintyBundle", "SCHEMA")
require("test_negative_proposition_is_preserved_not_deleted" in test and "test_main_app_mounts_v45_routes" in test, "TEST_COVERAGE")
require('assert version >= (4, 4, 0)' in v44_test, "V44_FORWARD_COMPATIBILITY")
print("PLATFORM_CORE_V4050_VALIDATION=PASS")
