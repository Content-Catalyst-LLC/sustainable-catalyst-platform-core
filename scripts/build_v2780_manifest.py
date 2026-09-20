#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

R = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache"}
files = []
for path in sorted(R.rglob("*")):
    if not path.is_file() or any(part in EXCLUDED_PARTS for part in path.parts) or path.name == "BUILD_MANIFEST.json":
        continue
    rel = path.relative_to(R).as_posix()
    files.append({
        "path": rel,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "size": path.stat().st_size,
    })
out = {"release": "2.78.0", "file_count": len(files), "files": files}
(R / "BUILD_MANIFEST.json").write_text(json.dumps(out, indent=2) + "\n")
print("manifest", len(files))
