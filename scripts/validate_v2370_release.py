#!/usr/bin/env python3
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
required=[
'RELEASE_NOTES_V2370.md','PLATFORM_CORE_V2370_INSTALL_AND_TEST.md','PLATFORM_CORE_V2370_CAUSAL_SYSTEMS_EXPLORER_AUDIT.md',
'backend/app/routers/causal_systems.py','backend/app/services/causal_systems.py','backend/tests/test_causal_systems_explorer_v2370.py','backend/tests/test_causal_systems_schema_compatibility_v2370.py','backend/scripts/validate_causal_systems.py',
'schemas/causal-graph-v1.schema.json','schemas/causal-variable-v1.schema.json','schemas/causal-edge-v1.schema.json','schemas/causal-intervention-v1.schema.json','schemas/causal-identification-v1.schema.json','schemas/causal-estimate-v1.schema.json','schemas/causal-diagnostic-v1.schema.json',
'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php','platform-core-v2370.env.example']
for rel in required:
    assert (ROOT/rel).is_file(),rel
cfg=(ROOT/'backend/app/config.py').read_text(); assert 'version: str = "2.37.0"' in cfg
mig=(ROOT/'backend/app/migrations.py').read_text(); assert '("0041", "Causal Systems Explorer' in mig
models=(ROOT/'backend/app/models.py').read_text()
for cls in ['CausalGraphRecord','CausalVariableRecord','CausalEdgeRecord','CausalInterventionRecord','CausalIdentificationRecord','CausalEstimateRecord','CausalDiagnosticRecord']:
    assert f'class {cls}' in models,cls
study=re.search(r'class SensitivityStudyRecord\(Base\):(.*?)(?=\nclass )',models,re.S).group(1)
assert 'id: Mapped[str]' in study and 'visual_entity_id' not in study
factor=re.search(r'class SensitivityFactorRecord\(Base\):(.*?)(?=\nclass )',models,re.S).group(1); assert 'study_id:' in factor
assert 'class SensitivityMeasureRecord' in models and 'class UncertaintyComputeRunRecord' in models
svc=(ROOT/'backend/app/services/causal_systems.py').read_text()
for guard in ["'automatic_causal_identification':False","'automatic_effect_estimation':False","'automatic_truth_promotion':False"]: assert guard in svc
wp=(ROOT/'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text(); assert 'Version: 2.37.0' in wp and "add_shortcode('sc_platform_core_causal_systems_status'" in wp
manifest=json.loads((ROOT/'BUILD_MANIFEST.json').read_text()); assert manifest['release']=='2.37.0' and manifest['file_count']==len(manifest['files'])
print('PASS - v2.37.0 Causal Systems Explorer release contract')
