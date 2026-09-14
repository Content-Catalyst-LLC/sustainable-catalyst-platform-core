#!/usr/bin/env python3
from pathlib import Path
import ast
ROOT=Path(__file__).resolve().parents[1]
CFG=(ROOT/'backend/app/config.py').read_text(); MIG=(ROOT/'backend/app/migrations.py').read_text(); MOD=(ROOT/'backend/app/models.py').read_text(); MAIN=(ROOT/'backend/app/main.py').read_text(); ROUTER=(ROOT/'backend/app/routers/open_forensics.py').read_text(); SERVICE=(ROOT/'backend/app/services/open_forensics.py').read_text(); WP=(ROOT/'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text(); SDKPY=(ROOT/'backend/public_sdk/python/sc_platform_core_public/client.py').read_text(); SDKJS=(ROOT/'backend/public_sdk/javascript/index.mjs').read_text(); PKG=(ROOT/'backend/public_sdk/javascript/package.json').read_text(); PYPROJECT=(ROOT/'backend/public_sdk/python/pyproject.toml').read_text()
assert 'version: str = "2.48.0"' in CFG and 'SustainableCatalystPlatformCore/2.48.0' in CFG
mod=ast.parse(MIG); migrations=None
for n in mod.body:
    if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MIGRATIONS' for t in n.targets): migrations=ast.literal_eval(n.value)
assert migrations; versions=[v for v,_ in migrations]; descriptions=dict(migrations); assert versions[-1]=='0052' and len(versions)==len(set(versions)); assert len(descriptions['0052'])<=300
for name in ['ForensicQuantitativeReconstructionRecord','ForensicQuantitativeMeasurementRecord','ForensicQuantitativeAssumptionRecord','ForensicQuantitativeParameterRecord','ForensicQuantitativeScenarioRecord','ForensicQuantitativeHandoffRecord','ForensicQuantitativeResultBindingRecord','ForensicQuantitativeReproductionPackageRecord']: assert f'class {name}' in MOD
for term in ['quantitative_reconstruction_registry_by_core','measurement_and_uncertainty_capture_by_core','assumption_parameter_registry_by_core','scenario_manifest_registry_by_core','workbench_lab_handoff_contracts_by_core','external_result_binding_by_core','reproducible_quantitative_packages_by_core','quantitative_model_execution_by_core','numerical_solution_by_core','statistical_inference_execution_by_core','uncertainty_propagation_execution_by_core','sensitivity_execution_by_core','parameter_optimization_by_core']: assert term in SERVICE
for term in ['/quantitative-reconstructions','/measurements','/assumptions','/parameters','/scenarios','/handoffs','/quantitative-handoffs/{handoff_id}/results','/reproduction-packages']: assert term in ROUTER
assert 'quantitative reconstruction & reproduction handoffs' in MAIN
assert 'Version: 2.48.0' in WP and 'sc_platform_core_forensic_quantitative_reconstruction_status' in WP
assert 'open_forensics_quantitative_reconstructions' in SDKPY and 'openForensicsQuantitativeReconstructions' in SDKJS
assert '"version": "2.48.0"' in PKG and 'version = "2.48.0"' in PYPROJECT
print(f"PASS - dependency-free release contract; migration ledger max=300, 0052 chars={len(descriptions['0052'])}")
print('PASS - v2.48.0 Quantitative Reconstruction & Reproduction Handoffs release contract')
