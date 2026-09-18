from pathlib import Path
import ast
R=Path(__file__).resolve().parents[1]
CFG=(R/'backend/app/config.py').read_text(); assert 'version: str = "2.72.0"' in CFG and 'SustainableCatalystPlatformCore/2.72.0' in CFG
mod=ast.parse((R/'backend/app/migrations.py').read_text()); m=[]
for n in mod.body:
 if isinstance(n,ast.Assign) and any(getattr(t,'id',None)=='MIGRATIONS' for t in n.targets): m=ast.literal_eval(n.value)
assert m[-1][0]=='0076' and len(m[-1][1])<=300
assert (R/'backend/app/routers/unified_research_projects.py').exists()
assert (R/'backend/app/services/unified_research_projects.py').exists()
assert (R/'schemas/unified-research-project-v1.schema.json').exists()
wp=(R/'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text(); rd=(R/'wordpress-plugin/sustainable-catalyst-platform-core/readme.txt').read_text(); assert 'Version: 2.72.0' in wp and "SCPC_VERSION', '2.72.0'" in wp and 'Stable tag: 2.72.0' in rd
py=(R/'backend/public_sdk/python/pyproject.toml').read_text(); js=(R/'backend/public_sdk/javascript/package.json').read_text(); assert 'version = "2.72.0"' in py and '"version": "2.72.0"' in js
print('PASS - dependency-free release contract; migration ledger max=300, 0076 chars='+str(len(m[-1][1])))
print('PASS - v2.72.0 Unified Research Project Object Model release contract')
