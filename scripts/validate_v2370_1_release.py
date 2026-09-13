#!/usr/bin/env python3
import json,sys,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
required=[
'RELEASE_NOTES_V2370_1.md','PLATFORM_CORE_V2370_1_INSTALL_AND_TEST.md','PLATFORM_CORE_V2370_1_CAUSAL_MIGRATION_METADATA_REPAIR_AUDIT.md',
'backend/app/routers/causal_systems.py','backend/app/services/causal_systems.py','backend/tests/test_causal_systems_explorer_v2370.py',
'backend/tests/test_causal_systems_schema_compatibility_v2370.py','backend/tests/test_partial_0041_recovery_v2370_1.py',
'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php','platform-core-v2370-1.env.example']
for rel in required: assert (ROOT/rel).is_file(),rel
cfg=(ROOT/'backend/app/config.py').read_text(); assert 'version: str = "2.37.0.1"' in cfg
wp=(ROOT/'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text(); assert 'Version: 2.37.0.1' in wp
sys.path.insert(0,str(ROOT/'backend'))
from app.migrations import MIGRATIONS
from app.models import SchemaMigration
max_len=SchemaMigration.__table__.c.description.type.length
assert max_len==300
violations=[(v,len(d)) for v,d in MIGRATIONS if len(d)>max_len]
assert not violations,violations
d=dict(MIGRATIONS)['0041']; assert len(d)<=300 and 'Causal Systems Explorer' in d
push=(ROOT/'PUSH_PLATFORM_CORE_V2370_1_FINAL.sh').read_text()
assert 'STOP: tag v2.37.0.1 already exists' in push
assert 'tag_commit' in push and 'head_commit' in push
manifest=json.loads((ROOT/'BUILD_MANIFEST.json').read_text()); assert manifest['release']=='2.37.0.1' and manifest['file_count']==len(manifest['files'])
print('PASS - v2.37.0.1 Causal Migration Metadata Repair release contract')
