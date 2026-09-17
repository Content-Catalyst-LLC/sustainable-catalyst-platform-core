#!/usr/bin/env python3
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
EXCLUDE_PREFIXES={'.git','backend/.venv'}; EXCLUDE_PARTS={'__pycache__','.pytest_cache'}
files=[]
for path in sorted(ROOT.rglob('*')):
    if not path.is_file(): continue
    rel=path.relative_to(ROOT).as_posix()
    if rel=='BUILD_MANIFEST.json' or any(rel==x or rel.startswith(x+'/') for x in EXCLUDE_PREFIXES) or any(part in EXCLUDE_PARTS for part in path.relative_to(ROOT).parts): continue
    if path.suffix in {'.db','.sqlite','.sqlite3'}: continue
    files.append({'path':rel,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
out={'release':'2.47.0','file_count':len(files),'files':files}; (ROOT/'BUILD_MANIFEST.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(f"PASS - v2.47.0 manifest written: {len(files)} files")
