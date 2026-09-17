#!/usr/bin/env python3
"""Dependency-free v2.37.0.2 release contract validation."""
import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
required = [
    'RELEASE_NOTES_V2370_2.md',
    'PLATFORM_CORE_V2370_2_INSTALL_AND_TEST.md',
    'PLATFORM_CORE_V2370_2_BUNDLE_VALIDATOR_BOOTSTRAP_REPAIR_AUDIT.md',
    'backend/app/routers/causal_systems.py',
    'backend/app/services/causal_systems.py',
    'backend/tests/test_causal_systems_explorer_v2370.py',
    'backend/tests/test_causal_systems_schema_compatibility_v2370.py',
    'backend/tests/test_partial_0041_recovery_v2370_1.py',
    'backend/tests/test_bundle_validator_bootstrap_v2370_2.py',
    'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php',
    'platform-core-v2370-2.env.example',
]
for rel in required:
    assert (ROOT / rel).is_file(), rel

cfg = (ROOT / 'backend/app/config.py').read_text()
assert 'version: str = "2.37.0.2"' in cfg
wp = (ROOT / 'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text()
assert 'Version: 2.37.0.2' in wp and "SCPC_VERSION', '2.37.0.2'" in wp

# Parse MIGRATIONS without importing app.migrations (and therefore SQLAlchemy).
mig_path = ROOT / 'backend/app/migrations.py'
tree = ast.parse(mig_path.read_text(), filename=str(mig_path))
migrations = None
for node in tree.body:
    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if any(isinstance(t, ast.Name) and t.id == 'MIGRATIONS' for t in targets):
            migrations = ast.literal_eval(node.value)
            break
assert migrations is not None and migrations, 'MIGRATIONS not found'
assert migrations[-1][0] == '0041', migrations[-1]

# Verify the production migration-ledger storage contract statically.
models = (ROOT / 'backend/app/models.py').read_text()
match = re.search(r'class\s+SchemaMigration\b.*?description:\s*Mapped\[str\]\s*=\s*mapped_column\(String\((\d+)\)', models, re.S)
assert match, 'SchemaMigration.description String length not found'
max_len = int(match.group(1))
assert max_len == 300, max_len
violations = [(v, len(d)) for v, d in migrations if len(d) > max_len]
assert not violations, violations
m41 = dict(migrations)['0041']
assert len(m41) <= max_len and 'Causal Systems Explorer' in m41

push = (ROOT / 'PUSH_PLATFORM_CORE_V2370_2_FINAL.sh').read_text()
assert 'STOP: tag v2.37.0.2 already exists' in push
assert 'tag_commit' in push and 'head_commit' in push

manifest = json.loads((ROOT / 'BUILD_MANIFEST.json').read_text())
assert manifest['release'] == '2.37.0.2'
assert manifest['file_count'] == len(manifest['files'])

print(f'PASS - dependency-free release contract; migration ledger max={max_len}, 0041 chars={len(m41)}')
print('PASS - v2.37.0.2 Bundle Validator Bootstrap Repair release contract')
