
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1]
exclude_parts={'.git','.venv','.pytest_cache','__pycache__','dist'}
files=[]
for p in sorted(R.rglob('*')):
    if not p.is_file() or p.name=='BUILD_MANIFEST.json' or p.suffix in {'.db','.pyc'} or any(x in exclude_parts for x in p.parts): continue
    b=p.read_bytes(); files.append({'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})
payload={'release':'2.22.0','file_count':len(files),'files':files}; (R/'BUILD_MANIFEST.json').write_text(json.dumps(payload,indent=2)+'\n'); print(f'PASS - v2.22.0 manifest built: {len(files)} files')
