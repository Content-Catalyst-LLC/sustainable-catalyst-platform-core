from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_DIRS = {".git", ".venv", ".pytest_cache", "__pycache__", "dist"}
EXCLUDED_FILES = {"BUILD_MANIFEST.json", "platform_core.db"}


def excluded(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if any(part in EXCLUDED_DIRS for part in rel.parts):
        return True
    if path.name in EXCLUDED_FILES or path.suffix in {".pyc", ".db"}:
        return True
    return False


def main() -> int:
    files = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or excluded(path):
            continue
        data = path.read_bytes()
        files.append({
            "path": path.relative_to(ROOT).as_posix(),
            "size_bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        })
    manifest = {
        "schema": "sc-release-manifest/1.0",
        "name": "sustainable-catalyst-platform-core-v2.9.0",
        "release": "2.9.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "file_count": len(files),
        "files": files,
    }
    (ROOT / "BUILD_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"PASS - wrote BUILD_MANIFEST.json with {len(files)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
