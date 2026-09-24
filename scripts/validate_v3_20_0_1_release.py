#!/usr/bin/env python3
import ast,re
from pathlib import Path
r=Path(__file__).resolve().parents[1]
needed=[
 r/'backend/scripts/ensure_investigation_workspace_schema_v3_20_0_1.py',
 r/'backend/scripts/validate_investigation_workspace_v3_20_0.py',
 r/'backend/app/routers/investigation_workspace.py', r/'V3_20_0_1_MIGRATION_ID.txt'
]
for p in needed: assert p.exists(), p
config=(r/'backend/app/config.py').read_text(); mig=(r/'backend/app/migrations.py').read_text(); php=(r/'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text()
assert '3.20.0.1' in config, 'backend config identity not repaired'
assert 'v3.20.0.1' in mig, 'repair migration not in ledger'
assert re.search(r'(?im)^\s*\*\s*Version:\s*3\.20\.0\.1',php), 'WordPress header not 3.20.0.1'
for p in [r/'backend/scripts/ensure_investigation_workspace_schema_v3_20_0_1.py',r/'backend/scripts/validate_investigation_workspace_v3_20_0.py']:
 ast.parse(p.read_text())
print('Platform Core v3.20.0.1 static validation: PASS')
