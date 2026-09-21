#!/usr/bin/env python3
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1]; out=R/"BUILD_MANIFEST.json"
skip={".git",".venv","__pycache__",".pytest_cache"}; files=[]
for p in sorted(R.rglob("*")):
 if not p.is_file() or p==out or any(x in skip for x in p.parts) or p.suffix.lower() in {".db",".sqlite",".sqlite3"}: continue
 rel=p.relative_to(R).as_posix(); files.append({"path":rel,"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"bytes":p.stat().st_size})
out.write_text(json.dumps({"release":"2.91.0","file_count":len(files),"files":files},indent=2)+"\n")
print(f"PASS - manifest written: {len(files)} files")
