#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDE_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache"}
EXCLUDE_NAMES = {"BUILD_MANIFEST.json", "platform_core.db", ".DS_Store"}
files = []
for path in sorted(ROOT.rglob("*")):
    if not path.is_file(): continue
    rel = path.relative_to(ROOT)
    if any(part in EXCLUDE_PARTS for part in rel.parts): continue
    if path.name in EXCLUDE_NAMES: continue
    files.append({"path": rel.as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "size": path.stat().st_size})
out = {"release": "2.40.0", "file_count": len(files), "files": files}
(ROOT / "BUILD_MANIFEST.json").write_text(json.dumps(out, indent=2) + "\n")
print(f"PASS - v2.40.0 manifest written: {len(files)} files")
