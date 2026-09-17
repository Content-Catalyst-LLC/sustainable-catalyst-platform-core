#!/usr/bin/env python3
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
EX={'.git','backend/.venv','__pycache__','.pytest_cache'}
files=[]
for p in sorted(R.rglob('*')):
 if not p.is_file() or any(x in p.parts for x in EX) or p.name=='BUILD_MANIFEST.json':continue
 rel=p.relative_to(R).as_posix();files.append({'path':rel,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size':p.stat().st_size})
out={'release':'2.69.0','file_count':len(files),'files':files};(R/'BUILD_MANIFEST.json').write_text(json.dumps(out,indent=2)+'\n');print('manifest',len(files))
