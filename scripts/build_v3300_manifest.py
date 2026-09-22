#!/usr/bin/env python3
from pathlib import Path
import hashlib, json
root=Path(__file__).resolve().parents[1]
files=[
 'backend/app/models.py','backend/app/migrations.py','backend/app/config.py','backend/app/main.py',
 'backend/app/services/statistical_reasoning.py','backend/app/routers/statistical_reasoning.py',
 'backend/tests/test_statistical_reasoning_v3300.py','backend/scripts/validate_statistical_reasoning.py',
 'backend/scripts/run_v3300_release_tests.py','scripts/validate_v3300_release.py',
 'schemas/statistical-reasoning-object-model-v1.schema.json','examples/statistical_reasoning_object_v330.json',
 'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php'
]
out={'release':'3.3.0','title':'Statistical Reasoning Object Model','migration':'0105','core_contract':'sc.core.statistical-reasoning-object-model.v1','source_contract':'sc.analytics-r.statistical-diagnostics-validation.v1','catalyst_analytics_r':'2.2.0','workspace_adapter':'3.9.1','files':{}}
for rel in files:
 p=root/rel; out['files'][rel]=hashlib.sha256(p.read_bytes()).hexdigest()
(root/'release-manifest-v3.3.0.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print('PASS - v3.3.0 manifest generated')
