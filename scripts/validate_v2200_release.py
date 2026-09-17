from pathlib import Path
import json,zipfile
R=Path(__file__).resolve().parents[1]
def req(x): p=R/x; assert p.exists(),x; return p
def has(x,t): assert t in req(x).read_text(),(x,t)
required=['backend/app/config.py','backend/app/models.py','backend/app/services/continuity.py','backend/app/routers/continuity.py','backend/app/migrations.py','backend/tests/test_continuity_disaster_recovery_v2200.py','backend/scripts/validate_continuity_disaster_recovery.py','deployment/platform-core-v2200.env.example','docs/CONTINUITY_BACKUP_VERIFICATION_DISASTER_RECOVERY_V2200.md','RELEASE_NOTES_V2200.md','PLATFORM_CORE_V2200_INSTALL_AND_TEST.md','PLATFORM_CORE_V2200_CONTINUITY_DISASTER_RECOVERY_AUDIT.md','PLATFORM_CORE_V2200_TERMINAL_COMMANDS.txt','schemas/backup-artifact-v1.schema.json','schemas/restore-rehearsal-v1.schema.json','render.yaml','wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php','backend/public_sdk/downloads/sc-platform-core-public-python-v2.20.0.zip','backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.20.0.zip']
for x in required:req(x)
has('backend/app/config.py','version: str = "2.20.0"'); has('backend/app/migrations.py','("0023",'); has('backend/app/main.py','continuity.public_router'); has('backend/app/routers/meta.py','continuity_backup_verification_disaster_recovery'); has('backend/app/services/continuity.py','automatic_restore=False'); has('backend/app/services/continuity.py','arbitrary_restore_commands_enabled'); has('backend/app/services/certification.py','certification_require_recent_verified_backup'); has('wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php','Version: 2.20.0'); has('render.yaml','SC_CORE_CONTINUITY_DISASTER_RECOVERY_ENABLED')
assert json.loads(req('backend/public_sdk/javascript/package.json').read_text())['version']=='2.20.0'; assert 'version = "2.20.0"' in req('backend/public_sdk/python/pyproject.toml').read_text()
for z in ['backend/public_sdk/downloads/sc-platform-core-public-python-v2.20.0.zip','backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.20.0.zip']:
    with zipfile.ZipFile(req(z)) as f: assert f.testzip() is None
for script in ['PUSH_PLATFORM_CORE_V2200_FINAL.sh','deploy_and_validate_platform_core_v2_20_0_macos.sh']:
    if (R/script).exists():
        text=(R/script).read_text(); assert 'v2.20.0' in text and 'v2_20_0' in text
print('PASS - v2.20.0 release contract')
