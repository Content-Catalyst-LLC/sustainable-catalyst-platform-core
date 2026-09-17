from pathlib import Path
import ast
R=Path(__file__).resolve().parents[1]
CFG=(R/'backend/app/config.py').read_text();assert 'version: str = "2.68.0"' in CFG and 'SustainableCatalystPlatformCore/2.68.0' in CFG
mod=ast.parse((R/'backend/app/migrations.py').read_text());m=[]
for n in mod.body:
 if isinstance(n,ast.Assign) and any(getattr(t,'id',None)=='MIGRATIONS' for t in n.targets):m=ast.literal_eval(n.value)
assert m[-1][0]=='0072' and len(m[-1][1])<=300
assert (R/'backend/app/routers/visual_forensics_workbench.py').exists()
assert (R/'backend/app/services/visual_forensics_workbench.py').exists()
print('PASS - dependency-free release contract; migration ledger max=300, 0072 chars='+str(len(m[-1][1])))
print('PASS - v2.68.0 Visual Forensics Workbench release contract')
