from __future__ import annotations

from pathlib import Path
import ast
import json

R = Path(__file__).resolve().parents[1]

def req(path: str) -> Path:
    p = R / path
    assert p.is_file(), path
    return p

def text(path: str) -> str:
    return req(path).read_text()

# R1 repairs promotion tooling only: runtime/schema remain v2.24.0 / 0027.
assert 'version: str = "2.24.0"' in text('backend/app/config.py')
assert '("0027", "Capacity resource profiles' in text('backend/app/migrations.py')
manifest = json.loads(text('BUILD_MANIFEST.json'))
assert manifest.get('release') == '2.24.0', manifest.get('release')

scanner = text('scripts/scan_push_safe_secrets.py')
assert 'replace-with-long-random-secret' in scanner
assert 'ALLOWED_FEDERATION_PLACEHOLDERS' in scanner
assert '_federation_assignment_is_documented_placeholder' in scanner
assert 'platform-core-v2231.env.example' not in scanner
assert 'EXCLUDED_SUFFIXES' in scanner

push = text('PUSH_PLATFORM_CORE_V2240_FINAL.sh')
deploy = text('deploy_and_validate_platform_core_v2_24_0_macos.sh')
for body in (push, deploy):
    assert 'scripts/validate_v2240_r1_promotion_repair.py' in body
    assert 'scripts/scan_push_safe_secrets.py' in body
assert "--exclude='platform-core-v2231.env.example'" not in push
assert 'repair_and_resume_platform_core_v2_24_0_r1_macos.sh' in push
assert 'repair_and_resume_platform_core_v2_24_0_r1_macos.sh' in deploy

for path in (
    'repair_and_resume_platform_core_v2_24_0_r1_macos.sh',
    'RELEASE_NOTES_V2240_R1.md',
    'PLATFORM_CORE_V2240_R1_SECRET_SCAN_PROMOTION_REPAIR_AUDIT.md',
    'PLATFORM_CORE_V2240_R1_INSTALL_AND_TEST.md',
    'PLATFORM_CORE_V2240_R1_TERMINAL_COMMANDS.txt',
    'backend/tests/test_secret_scan_promotion_repair_v2240_r1.py',
):
    req(path)

ast.parse(scanner)
ast.parse(text('backend/tests/test_secret_scan_promotion_repair_v2240_r1.py'))
print('PASS - v2.24.0 R1 secret-scan example credential and promotion repair contract')
