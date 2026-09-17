from pathlib import Path
import ast
R=Path(__file__).resolve().parents[1]
CFG=(R/"backend/app/config.py").read_text();assert 'version: str = "2.69.0"' in CFG and 'SustainableCatalystPlatformCore/2.69.0' in CFG
mod=ast.parse((R/"backend/app/migrations.py").read_text());m=[]
for n in mod.body:
 if isinstance(n,ast.Assign) and any(getattr(t,"id",None)=="MIGRATIONS" for t in n.targets):m=ast.literal_eval(n.value)
assert m[-1][0]=="0073" and len(m[-1][1])<=300
assert (R/"backend/app/routers/visual_decision_intelligence.py").exists();assert (R/"backend/app/services/visual_decision_intelligence.py").exists()
print("PASS - dependency-free release contract; migration ledger max=300, 0073 chars="+str(len(m[-1][1])))
print("PASS - v2.69.0 Visual Decision Intelligence release contract")
