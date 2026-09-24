#!/usr/bin/env python3
import ast,re,sys
from pathlib import Path
r=Path(__file__).resolve().parents[1]
checks=[r/'backend/app/services/investigation_workspace.py',r/'backend/app/routers/investigation_workspace.py',r/'docs/UNIFIED_INVESTIGATION_WORKSPACE_V3_20_0.md',r/'wordpress-plugin/sustainable-catalyst-platform-core/includes/class-sc-core-investigation-workspace.php']
for p in checks:
    assert p.exists(), p
models=(r/'backend/app/models.py').read_text(); main=(r/'backend/app/main.py').read_text(); mig=(r/'backend/app/migrations.py').read_text(); php=(r/'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text()
for table in ['investigation_workspaces','investigation_workspace_objects','investigation_workspace_relations','investigation_workspace_views','investigation_workspace_snapshots','investigation_workspace_handoffs']: assert table in models, table
assert '_sc320_investigation_workspace' in main and 'include_router' in main
assert 'Unified Investigation Workspace' in mig
assert 'class-sc-core-investigation-workspace.php' in php
assert re.search(r'(?im)^\s*\*\s*Version:\s*3\.20\.0',php), 'WP header not v3.20.0'
ast.parse((r/'backend/app/models.py').read_text()); ast.parse((r/'backend/app/main.py').read_text()); ast.parse((r/'backend/app/routers/investigation_workspace.py').read_text()); ast.parse((r/'backend/app/services/investigation_workspace.py').read_text())
print('Platform Core v3.20.0 static validation: PASS')
