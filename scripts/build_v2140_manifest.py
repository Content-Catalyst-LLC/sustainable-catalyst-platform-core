from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
EXCLUDE={'.git','.venv','.pytest_cache','__pycache__','dist'}
def ok(p): return not any(part in EXCLUDE for part in p.parts) and p.suffix not in {'.pyc'} and not p.name.endswith('.db') and p.name!='BUILD_MANIFEST.json'
files=[]
for p in sorted(ROOT.rglob('*')):
    rel=p.relative_to(ROOT)
    if p.is_file() and ok(rel): files.append({'path':rel.as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})
payload={'release':'2.14.0','file_count':len(files),'files':files}
(ROOT/'BUILD_MANIFEST.json').write_text(json.dumps(payload,indent=2)+'\n')
print(f"PASS - v2.14.0 manifest built: {len(files)} files")
