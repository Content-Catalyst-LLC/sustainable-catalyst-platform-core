from pathlib import Path
import ast

R = Path(__file__).resolve().parents[1]

def req(path: str) -> Path:
    p = R / path
    assert p.exists(), path
    return p

def text(path: str) -> str:
    return req(path).read_text()

# Runtime version remains 2.18.0; R1 is promotion/test-lineage repair only.
assert 'version: str = "2.18.0"' in text('backend/app/config.py')
assert '("0021",' in text('backend/app/migrations.py')

# The inherited certification rehearsal must model a true migration-0019 state.
test_text = text('backend/tests/test_production_certification_v2170.py')
assert 'test_upgrade_from_recorded_0019_state_applies_current_head' in test_text
assert "if version <= '0019':" in test_text
assert "run_migrations(d)==['0020','0021']" in test_text
assert "if version!='0020'" not in test_text

# Promotion scripts must validate current lineage, not the prior v2.17 installer.
push_text = text('PUSH_PLATFORM_CORE_V2180_FINAL.sh')
assert 'scripts/validate_v2180_r1_promotion_repair.py' in push_text
assert 'bash -n deploy_and_validate_platform_core_v2_18_0_macos.sh' in push_text
assert 'bash -n repair_and_resume_platform_core_v2_18_0_r1_macos.sh' in push_text
assert 'bash -n deploy_and_validate_platform_core_v2_17_0_macos.sh' not in push_text

installer_text = text('deploy_and_validate_platform_core_v2_18_0_macos.sh')
assert 'scripts/validate_v2180_r1_promotion_repair.py' in installer_text
assert 'bash -n deploy_and_validate_platform_core_v2_18_0_macos.sh' in installer_text
assert 'bash -n repair_and_resume_platform_core_v2_18_0_r1_macos.sh' in installer_text
assert 'bash -n deploy_and_validate_platform_core_v2_17_0_macos.sh' not in installer_text

# Syntax sanity for the repaired historical test file.
ast.parse(test_text)
print('PASS - v2.18.0 R1 certification migration lineage and promotion repair contract')
