from pathlib import Path
import ast
R=Path(__file__).resolve().parents[1]
CFG=(R/"backend/app/config.py").read_text();assert 'version: str = "2.70.0"' in CFG and 'SustainableCatalystPlatformCore/2.70.0' in CFG
mod=ast.parse((R/"backend/app/migrations.py").read_text());m=[]
for n in mod.body:
 if isinstance(n,ast.Assign) and any(getattr(t,"id",None)=="MIGRATIONS" for t in n.targets):m=ast.literal_eval(n.value)
assert m[-1][0]=="0074" and len(m[-1][1])<=300
assert (R/"backend/app/routers/unified_visual_reasoning.py").exists();assert (R/"backend/app/services/unified_visual_reasoning.py").exists();assert (R/"schemas/unified-visual-reasoning-engine-v1.schema.json").exists()
wp=(R/"wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php").read_text();rd=(R/"wordpress-plugin/sustainable-catalyst-platform-core/readme.txt").read_text();assert 'Version: 2.70.0' in wp and "SCPC_VERSION', '2.70.0'" in wp and 'Stable tag: 2.70.0' in rd
print("PASS - dependency-free release contract; migration ledger max=300, 0074 chars="+str(len(m[-1][1])))
print("PASS - v2.70.0 Unified Visual Reasoning Engine release contract")
