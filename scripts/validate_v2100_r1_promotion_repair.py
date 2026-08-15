from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUSH = ROOT / "PUSH_PLATFORM_CORE_V2100_FINAL.sh"
MANIFEST = ROOT / "BUILD_MANIFEST.json"


def main() -> None:
    push = PUSH.read_text()
    manifest = json.loads(MANIFEST.read_text())

    assert manifest.get("release") == "2.10.0", manifest.get("release")
    assert "assert m.get('release')=='2.10.0'" in push
    assert "assert m.get('release')=='2.9.0'" not in push
    assert "bash -n deploy_and_validate_platform_core_v2_10_0_macos.sh" in push
    assert "bash -n deploy_and_validate_platform_core_v2_9_0_macos.sh" not in push
    assert "backend/tests/test_streaming_alerts_reliability_v290.py" in push
    assert "backend/tests/test_streaming_alerts_reliability_v2100.py" not in push

    required = [
        ROOT / "deploy_and_validate_platform_core_v2_10_0_macos.sh",
        ROOT / "backend/tests/test_streaming_alerts_reliability_v290.py",
        ROOT / "backend/tests/test_operational_facilities_v2100.py",
        ROOT / "scripts/validate_v2100_release.py",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    assert not missing, missing

    print("PASS - v2.10.0 R1 promotion repair contract")


if __name__ == "__main__":
    main()
