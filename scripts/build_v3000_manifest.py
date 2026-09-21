#!/usr/bin/env python3
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1]
exclude={".git",".venv","__pycache__",".pytest_cache"}
files=[]
for p in sorted(R.rglob("*")):
 if not p.is_file(): continue
 rel=p.relative_to(R)
 if any(x in exclude for x in rel.parts): continue
 if p.suffix in {".db",".sqlite",".sqlite3",".pyc"}: continue
 if rel.as_posix()=="BUILD_MANIFEST.json": continue
 files.append({"path":rel.as_posix(),"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"size":p.stat().st_size})
(R/"BUILD_MANIFEST.json").write_text(json.dumps({"release":"3.0.0","files":files},indent=2)+"\n")
print(f"PASS - v3.0.0 manifest generated: {len(files)} files")
