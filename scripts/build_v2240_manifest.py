from pathlib import Path
import hashlib
import json

R = Path(__file__).resolve().parents[1]
exclude_parts = {".git", ".venv", ".pytest_cache", "__pycache__", "dist"}
files = []
for path in sorted(R.rglob("*")):
    if (
        not path.is_file()
        or path.name == "BUILD_MANIFEST.json"
        or path.suffix in {".db", ".pyc"}
        or any(part in exclude_parts for part in path.parts)
    ):
        continue
    payload = path.read_bytes()
    files.append({"path": path.relative_to(R).as_posix(), "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)})
manifest = {"release": "2.24.0", "file_count": len(files), "files": files}
(R / "BUILD_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(f"PASS - v2.24.0 manifest built: {len(files)} files")
