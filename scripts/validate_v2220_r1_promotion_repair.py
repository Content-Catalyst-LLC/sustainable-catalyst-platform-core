from pathlib import Path
import ast
import re

R = Path(__file__).resolve().parents[1]

def req(path: str) -> Path:
    p = R / path
    assert p.is_file(), path
    return p

def text(path: str) -> str:
    return req(path).read_text()

# R1 is promotion/test-lineage repair only. Runtime/schema stay frozen at v2.22.0 / 0025.
assert 'version: str = "2.22.0"' in text('backend/app/config.py')
assert '("0025",' in text('backend/app/migrations.py')

# v2.21 resilience rehearsal must model a true 0023 state and apply every later migration.
resilience_test = text('backend/tests/test_multi_region_resilience_v2210.py')
assert 'test_migration_rehearsal_from_0023_applies_current_head' in resilience_test
assert "if version<='0023'" in resilience_test
assert "expected=[version for version,_ in MIGRATIONS if version>'0023']" in resilience_test
assert "run_migrations(d)==['0024']" not in resilience_test

# Harden the current v2.22 rehearsal now so v2.23+ does not repeat the same failure.
lifecycle_test = text('backend/tests/test_data_lifecycle_preservation_v2220.py')
assert 'test_migration_rehearsal_from_0024_applies_current_head' in lifecycle_test
assert "if version<='0024'" in lifecycle_test
assert "expected=[version for version,_ in MIGRATIONS if version>'0024']" in lifecycle_test
assert "run_migrations(d)==['0025']" not in lifecycle_test

# No active migration rehearsal may hard-code a single next migration result.
for p in sorted((R / 'backend/tests').glob('test_*.py')):
    s = p.read_text()
    if 'run_migrations(' not in s:
        continue
    bad = re.findall(r"run_migrations\([^)]*\)\s*==\s*\[['\"]00\d+['\"]\]", s)
    assert not bad, f'stale exact migration-head assertion in {p.name}: {bad}'

# Promotion scripts must enforce R1 preflight and syntax-check the repair wrapper.
for script in ['PUSH_PLATFORM_CORE_V2220_FINAL.sh', 'deploy_and_validate_platform_core_v2_22_0_macos.sh']:
    s = text(script)
    assert 'scripts/validate_v2220_r1_promotion_repair.py' in s
    assert 'bash -n repair_and_resume_platform_core_v2_22_0_r1_macos.sh' in s

ast.parse(resilience_test)
ast.parse(lifecycle_test)
print('PASS - v2.22.0 R1 resilience migration lineage and promotion repair contract')
