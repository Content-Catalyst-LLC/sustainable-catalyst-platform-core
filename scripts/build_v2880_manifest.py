#!/usr/bin/env python3
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1]; out={}
for p in sorted(x for x in R.rglob('*') if x.is_file() and '.git' not in x.parts and '__pycache__' not in x.parts and x.name!='BUILD_MANIFEST.json' and '.pytest_cache' not in x.parts and not x.name.endswith('.db') and '.venv' not in x.parts):
 rel=p.relative_to(R).as_posix(); out[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
(R/'BUILD_MANIFEST.json').write_text(json.dumps({'release':'2.88.0','file_count':len(out),'sha256':out},indent=2,sort_keys=True)+'\n')
print(f"PASS - wrote BUILD_MANIFEST.json for {len(out)} files")
