from pathlib import Path
import ast
R=Path(__file__).resolve().parents[1]
CFG=(R/'backend/app/config.py').read_text(); assert 'version: str = "2.73.0"' in CFG and 'SustainableCatalystPlatformCore/2.73.0' in CFG
mod=ast.parse((R/'backend/app/migrations.py').read_text()); m=[]
for n in mod.body:
 if isinstance(n,ast.Assign) and any(getattr(t,'id',None)=='MIGRATIONS' for t in n.targets): m=ast.literal_eval(n.value)
assert m[-1][0]=='0077' and len(m[-1][1])<=300
for f in ('backend/app/routers/research_lineage.py','backend/app/services/research_lineage.py','schemas/research-lineage-v1.schema.json'): assert (R/f).exists(),f
wp=(R/'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text(); rd=(R/'wordpress-plugin/sustainable-catalyst-platform-core/readme.txt').read_text(); assert 'Version: 2.73.0' in wp and "SCPC_VERSION', '2.73.0'" in wp and 'Stable tag: 2.73.0' in rd
py=(R/'backend/public_sdk/python/pyproject.toml').read_text(); js=(R/'backend/public_sdk/javascript/package.json').read_text(); assert 'version = "2.73.0"' in py and '"version": "2.73.0"' in js
print('PASS - dependency-free release contract; migration ledger max=300, 0077 chars='+str(len(m[-1][1])))
print('PASS - v2.73.0 Research Lineage & Provenance Graph release contract')
