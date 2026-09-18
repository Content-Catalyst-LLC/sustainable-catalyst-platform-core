from pathlib import Path
import ast
R=Path(__file__).resolve().parents[1]
CFG=(R/'backend/app/config.py').read_text(); assert 'version: str = "2.71.0"' in CFG and 'SustainableCatalystPlatformCore/2.71.0' in CFG
mod=ast.parse((R/'backend/app/migrations.py').read_text()); m=[]
for n in mod.body:
 if isinstance(n,ast.Assign) and any(getattr(t,'id',None)=='MIGRATIONS' for t in n.targets): m=ast.literal_eval(n.value)
assert m[-1][0]=='0075' and len(m[-1][1])<=300
assert (R/'backend/app/routers/cross_product_visual_runtime_integration.py').exists()
assert (R/'backend/app/services/cross_product_visual_runtime_integration.py').exists()
assert (R/'schemas/cross-product-visual-runtime-integration-v1.schema.json').exists()
wp=(R/'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text(); rd=(R/'wordpress-plugin/sustainable-catalyst-platform-core/readme.txt').read_text(); assert 'Version: 2.71.0' in wp and "SCPC_VERSION', '2.71.0'" in wp and 'Stable tag: 2.71.0' in rd
py=(R/'backend/public_sdk/python/pyproject.toml').read_text(); js=(R/'backend/public_sdk/javascript/package.json').read_text(); assert 'version = "2.71.0"' in py and '"version": "2.71.0"' in js
print('PASS - dependency-free release contract; migration ledger max=300, 0075 chars='+str(len(m[-1][1])))
print('PASS - v2.71.0 Cross-Product Visual Runtime Integration release contract')
