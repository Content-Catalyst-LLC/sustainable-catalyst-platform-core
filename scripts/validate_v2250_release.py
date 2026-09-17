from __future__ import annotations

from pathlib import Path
import json
import re
import zipfile

R = Path(__file__).resolve().parents[1]

def req(path: str) -> Path:
    p = R / path
    assert p.is_file(), path
    return p

def has(path: str, text: str) -> None:
    assert text in req(path).read_text(), (path, text)

required = [
    "backend/app/config.py",
    "backend/app/models.py",
    "backend/app/migrations.py",
    "backend/app/routers/credentials.py",
    "backend/app/services/credentials.py",
    "backend/app/services/certification.py",
    "backend/scripts/validate_credential_key_lifecycle.py",
    "backend/tests/test_identity_credential_key_lifecycle_v2250.py",
    "schemas/credential-registry-v1.schema.json",
    "schemas/credential-key-version-v1.schema.json",
    "docs/IDENTITY_CREDENTIAL_KEY_LIFECYCLE_V2250.md",
    "RELEASE_NOTES_V2250.md",
    "PLATFORM_CORE_V2250_INSTALL_AND_TEST.md",
    "PLATFORM_CORE_V2250_IDENTITY_CREDENTIAL_KEY_LIFECYCLE_AUDIT.md",
    "PLATFORM_CORE_V2250_TERMINAL_COMMANDS.txt",
    "deployment/platform-core-v2250.env.example",
    "render.yaml",
    "wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php",
    "backend/public_sdk/downloads/sc-platform-core-public-python-v2.25.0.zip",
    "backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.25.0.zip",
    "PUSH_PLATFORM_CORE_V2250_FINAL.sh",
    "deploy_and_validate_platform_core_v2_25_0_macos.sh",
]
for path in required: req(path)

has("backend/app/config.py", 'version: str = "2.25.0"')
has("backend/app/migrations.py", '("0028", "Credential registry metadata')
has("backend/app/main.py", "credentials.public_router")
has("backend/app/routers/meta.py", '"identity_credential_key_lifecycle"')
has("backend/app/routers/credentials.py", 'prefix="/v1/credentials"')
has("backend/app/routers/credentials.py", 'prefix="/api/v1/credentials"')
has("backend/app/services/credentials.py", 'SAFE_REFERENCE_PREFIXES')
has("backend/app/services/credentials.py", '"automatic_secret_generation": False')
has("backend/app/services/credentials.py", '"automatic_secret_distribution": False')
has("backend/app/services/credentials.py", '"automatic_key_rotation": False')
has("backend/app/services/certification.py", "certification_require_credential_lifecycle_ready")
has("wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php", "Version: 2.25.0")
has("wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php", "sc_platform_core_credential_lifecycle_status")
has("render.yaml", "SustainableCatalystPlatformCore/2.25.0")
has("render.yaml", "SC_CORE_CREDENTIAL_KEY_LIFECYCLE_ENABLED")
has("render.yaml", "SC_CORE_CERTIFICATION_REQUIRE_CREDENTIAL_LIFECYCLE_READY")
assert json.loads(req("backend/public_sdk/javascript/package.json").read_text())["version"] == "2.25.0"
assert 'version = "2.25.0"' in req("backend/public_sdk/python/pyproject.toml").read_text()
assert req("README.md").read_text().startswith("# Sustainable Catalyst Platform Core v2.25.0")
has("docs/ROADMAP.md", "v2.25.0 — Identity, Credential & Cryptographic Key Lifecycle")
has("docs/ROADMAP.md", "Next planned: v2.26.0 — Distributed Quotas, Admission Control & Workload Governance")

meta = req("backend/app/routers/meta.py").read_text()
implemented_block = meta.split("capabilities=[", 1)[1].split("deferred_capabilities=[", 1)[0]
deferred_block = meta.split("deferred_capabilities=[", 1)[1].split("]", 1)[0]
implemented = re.findall(r'"([a-z0-9_]+)"', implemented_block)
deferred = re.findall(r'"([a-z0-9_]+)"', deferred_block)
assert len(implemented) == len(set(implemented)), "duplicate implemented capability"
assert len(deferred) == len(set(deferred)), "duplicate deferred capability"
assert set(implemented).isdisjoint(deferred), "implemented/deferred overlap"
for capability in (
    "identity_credential_key_lifecycle",
    "secret_free_credential_registry",
    "cryptographic_key_version_metadata",
    "credential_expiry_and_revocation",
    "overlap_aware_key_rotation",
    "credential_use_audit_events",
    "public_safe_credential_health",
    "credential_lifecycle_certification_gate",
):
    assert capability in implemented, capability
    assert capability not in deferred, capability
assert "external_public_key_signature_verification" in deferred

for schema in ("schemas/credential-registry-v1.schema.json", "schemas/credential-key-version-v1.schema.json"):
    json.loads(req(schema).read_text())

for z in (
    "backend/public_sdk/downloads/sc-platform-core-public-python-v2.25.0.zip",
    "backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.25.0.zip",
):
    with zipfile.ZipFile(req(z)) as archive:
        assert archive.testzip() is None

for script in ("PUSH_PLATFORM_CORE_V2250_FINAL.sh", "deploy_and_validate_platform_core_v2_25_0_macos.sh"):
    text = req(script).read_text()
    assert "v2.25.0" in text and "v2250" in text
    assert "validate_credential_key_lifecycle.py" in text
    assert "scan_push_safe_secrets.py" in text

print("PASS - v2.25.0 identity credential and cryptographic key lifecycle release contract")
