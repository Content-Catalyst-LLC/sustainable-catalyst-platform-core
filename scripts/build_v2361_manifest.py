#!/usr/bin/env python3
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
EXCLUDED_DIRS={'.git','.venv','__pycache__','.pytest_cache','dist','var'}
EXCLUDED_SUFFIXES={'.pyc','.db'}
items=[]
for p in sorted(ROOT.rglob('*')):
    if not p.is_file(): continue
    rel=p.relative_to(ROOT)
    if any(part in EXCLUDED_DIRS for part in rel.parts): continue
    if p.suffix in EXCLUDED_SUFFIXES: continue
    if rel.name in {'BUILD_MANIFEST.json','MANIFEST.sha256'}: continue
    data=p.read_bytes(); items.append({'path':rel.as_posix(),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
manifest={'release':'2.36.1','file_count':len(items),'files':items}
(ROOT/'BUILD_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
(ROOT/'MANIFEST.sha256').write_text('\n'.join(f"{x['sha256']}  {x['path']}" for x in items)+'\n')
print(f"PASS - v2.36.1 manifest built across {len(items)} files")
