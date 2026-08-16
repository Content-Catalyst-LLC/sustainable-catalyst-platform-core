from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCANNER_PATH = ROOT / "scripts" / "scan_push_safe_secrets.py"
spec = importlib.util.spec_from_file_location("scan_push_safe_secrets", SCANNER_PATH)
scanner = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(scanner)


def test_inherited_documented_federation_placeholder_is_allowed():
    line = '# SC_CORE_FEDERATION_TRUST_SECRETS_JSON={"remote-node-id":"replace-with-long-random-secret"}'
    assert scanner.scan_text(Path("deployment/platform-core-v2231.env.example"), line) == []


def test_live_federation_secret_in_env_example_is_rejected():
    line = '# SC_CORE_FEDERATION_TRUST_SECRETS_JSON={"remote-node-id":"v7GQm2xE9bK4rP8sN1cT6zW3yH5jL0qA"}'
    hits = scanner.scan_text(Path("deployment/example.env.example"), line)
    assert hits and hits[0][1] == "federation_trust_json"


def test_placeholder_prefix_with_extra_secret_material_is_rejected():
    line = '# SC_CORE_FEDERATION_TRUST_SECRETS_JSON={"remote-node-id":"replace-with-long-random-secret-ACTUALVALUE"}'
    hits = scanner.scan_text(Path("deployment/example.env.example"), line)
    assert hits and hits[0][1] == "federation_trust_json"


def test_openai_like_token_is_rejected():
    token = "sk-proj-" + ("A" * 32)
    hits = scanner.scan_text(Path("notes.txt"), f"OPENAI_API_KEY={token}")
    assert hits and hits[0][1] == "openai_key"


def test_repository_scanner_accepts_current_documented_examples():
    assert scanner.scan_repository(ROOT) == []
