from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(path: str) -> Path:
    p = ROOT / path
    if not p.is_file():
        raise SystemExit(f"ERROR - required R1 file missing: {path}")
    return p


def main() -> None:
    manifest = json.loads(require("BUILD_MANIFEST.json").read_text())
    assert manifest.get("release") == "2.14.0", manifest.get("release")

    validators = {
        "backend/scripts/validate_streaming_reliability.py": "version_tuple(settings.version) < (2, 9, 0)",
        "backend/scripts/validate_operational_facilities.py": "version >= (2,10,0)",
        "backend/scripts/validate_country_evidence.py": "version >= (2,12,0)",
        "backend/scripts/validate_scientific_service_fabric.py": "version >= (2,13,0)",
    }
    for path, marker in validators.items():
        text = require(path).read_text()
        assert marker in text, f"forward-compatible version gate missing from {path}"
        assert "settings.version=='2.13.0'" not in text, f"stale exact 2.13.0 gate in {path}"
        assert 'settings.version != "2.13.0"' not in text, f"stale exact 2.13.0 gate in {path}"

    push = require("PUSH_PLATFORM_CORE_V2140_FINAL.sh").read_text()
    deploy = require("deploy_and_validate_platform_core_v2_14_0_macos.sh").read_text()
    for target in (
        "backend/scripts/validate_streaming_reliability.py",
        "backend/scripts/validate_operational_facilities.py",
        "backend/scripts/validate_humanitarian_access.py",
        "backend/scripts/validate_country_evidence.py",
        "backend/scripts/validate_scientific_service_fabric.py",
        "backend/scripts/validate_cross_product_exchange.py",
    ):
        assert target in push, f"push validator target missing: {target}"
        assert target in deploy, f"deploy validator target missing: {target}"
        require(target)

    assert "scripts/validate_v2140_r1_promotion_repair.py" in push
    assert "scripts/validate_v2140_r1_promotion_repair.py" in deploy
    assert "assert m.get('release')=='2.14.0'" in push
    assert 'assert m["release"]=="2.14.0"' in deploy

    # R1 is promotion-lineage only: the canonical runtime version and migration remain v2.14.0/0017.
    config = require("backend/app/config.py").read_text()
    migrations = require("backend/app/migrations.py").read_text()
    assert 'version: str = "2.14.0"' in config
    assert '("0017", "Cross-product evidence exchange' in migrations

    print("PASS - v2.14.0 R1 promotion repair contract")


if __name__ == "__main__":
    main()
