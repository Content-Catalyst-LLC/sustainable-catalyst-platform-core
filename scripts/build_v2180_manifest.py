from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1]
exclude={'.git','.venv','.pytest_cache','__pycache__','dist'}
files=[]
for p in sorted(R.rglob('*')):
 if not p.is_file() or any(part in exclude for part in p.parts): continue
 if p.name=='BUILD_MANIFEST.json' or p.suffix in {'.pyc','.db'}: continue
 rel=p.relative_to(R).as_posix(); files.append({'path':rel,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})
payload={'release':'2.18.0','file_count':len(files),'files':files}; (R/'BUILD_MANIFEST.json').write_text(json.dumps(payload,indent=2)+'\n')
print(f"PASS - v2.18.0 manifest built: {len(files)} files")
