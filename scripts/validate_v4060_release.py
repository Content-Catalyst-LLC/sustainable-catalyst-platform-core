from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, label: str) -> None:
    if not condition:
        raise SystemExit(f"PLATFORM_CORE_V4060_{label}=FAIL")
    print(f"PLATFORM_CORE_V4060_{label}=PASS")


config = (ROOT / "backend/app/config.py").read_text()
main = (ROOT / "backend/app/main.py").read_text()
service = (ROOT / "backend/app/services/pragmatic_meaning_speech_act_intent.py").read_text()
router = (ROOT / "backend/app/routers/pragmatic_meaning_speech_act_intent.py").read_text()
test = (ROOT / "backend/tests/test_pragmatic_meaning_speech_act_intent_v4060.py").read_text()
v45_test = (ROOT / "backend/tests/test_epistemic_modal_negation_certainty_v4050.py").read_text()
readme = (ROOT / "README.md").read_text()
wp = (ROOT / "wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php").read_text()
wp_readme = (ROOT / "wordpress-plugin/sustainable-catalyst-platform-core/readme.txt").read_text()
schema = json.loads((ROOT / "schemas/sc-core-pragmatic-meaning-speech-act-communicative-intent-v1.schema.json").read_text())

require('version: str = "4.6.0"' in config, "BACKEND_VERSION")
require("pragmatic_meaning_speech_act_intent," in main and "pragmatic_meaning_speech_act_intent.router" in main and "pragmatic_meaning_speech_act_intent.public_router" in main, "ROUTE_MOUNT")
require('CORE_RELEASE = "4.6.0"' in service, "SERVICE_RELEASE")
require('CONTRACT_VERSION = "sc.core.pragmatic-meaning-speech-act-communicative-intent.v1"' in service, "CONTRACT")
require('prefix="/v1/pragmatic-semantics"' in router and 'prefix="/public/v1/pragmatic-semantics"' in router, "API_SURFACE")
require(all(name in service for name in ["CommunicativeParticipant", "PragmaticContentUnit", "PragmaticCue", "PragmaticContext", "SpeechAct", "CommunicativeIntent"]), "OBJECT_FOUNDATION")
require('"assertion_establishes_platform_truth": False' in service and '"request_creates_platform_obligation": False' in service, "PRAGMATIC_BOUNDARY")
require('"communicative_intent_reveals_private_mental_state": False' in service and '"surface_speaker_establishes_canonical_actor_identity": False' in service, "INTENT_IDENTITY_BOUNDARY")
require('**Current release:** v4.6.0 — Pragmatic Meaning, Speech Act & Communicative Intent' in readme, "README")
require(" * Version: 4.6.0" in wp and "define('SCPC_VERSION', '4.6.0');" in wp, "WORDPRESS_VERSION")
require("Stable tag: 4.6.0" in wp_readme, "WORDPRESS_STABLE_TAG")
require(schema.get("title") == "PragmaticMeaningSpeechActIntentBundle", "SCHEMA")
require("test_reference_speech_act_types" in test and "test_main_app_mounts_v46_routes" in test, "TEST_COVERAGE")
require('assert version >= (4, 5, 0)' in v45_test, "V45_FORWARD_COMPATIBILITY")
print("PLATFORM_CORE_V4060_VALIDATION=PASS")
