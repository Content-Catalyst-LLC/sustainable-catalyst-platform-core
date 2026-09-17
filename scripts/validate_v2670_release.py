#!/usr/bin/env python3
from pathlib import Path
import ast,json
ROOT=Path(__file__).resolve().parents[1]
CFG=(ROOT/'backend/app/config.py').read_text();MIG=(ROOT/'backend/app/migrations.py').read_text();MAIN=(ROOT/'backend/app/main.py').read_text();WP=(ROOT/'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text();PKG=(ROOT/'backend/public_sdk/javascript/package.json').read_text();PYPROJ=(ROOT/'backend/public_sdk/python/pyproject.toml').read_text();SVC=(ROOT/'backend/app/services/visual_predictive_intelligence.py').read_text();ROUTER=(ROOT/'backend/app/routers/visual_predictive_intelligence.py').read_text();MODELS=(ROOT/'backend/app/models.py').read_text();SCHEMA=json.loads((ROOT/'schemas/visual-predictive-workspace-v1.schema.json').read_text())
assert 'version: str = "2.67.0"' in CFG and 'SustainableCatalystPlatformCore/2.67.0' in CFG
assert 'visual_predictive_intelligence' in MAIN and 'visual_predictive_intelligence_enabled' in CFG
module=ast.parse(MIG);migrations=None
for n in module.body:
 if isinstance(n,ast.Assign) and any(getattr(t,'id',None)=='MIGRATIONS' for t in n.targets):migrations=ast.literal_eval(n.value)
assert migrations and migrations[-1][0]=='0071' and len(migrations[-1][1])<=300
assert 'Version: 2.67.0' in WP and 'sc_platform_core_visual_predictive_status' in WP
assert '"version": "2.67.0"' in PKG and 'version = "2.67.0"' in PYPROJ
for marker in ('VisualPredictiveWorkspaceRecord','VisualForecastOverlayRecord','VisualUncertaintyDisplayRecord','VisualCalibrationDisplayRecord','VisualEnsembleComparisonOverlayRecord','VisualMonitoringOverlayRecord','VisualSpatialTemporalForecastLayerRecord','VisualCausalPredictiveOverlayRecord','VisualDecisionPredictionBindingRecord','VisualPredictiveSnapshotRecord'):assert marker in MODELS,marker
for marker in ('visual_predictive_workspace_registry_by_core','visual_forecast_overlay_registry_by_core','visual_uncertainty_display_registry_by_core','visual_calibration_display_registry_by_core','visual_ensemble_comparison_registry_by_core','visual_monitoring_overlay_registry_by_core','visual_spatial_temporal_forecast_registry_by_core','visual_causal_predictive_overlay_registry_by_core','visual_decision_prediction_binding_registry_by_core','immutable_visual_predictive_snapshots_by_core','forecast_execution_by_core','decision_optimization_by_core','visual_rendering_by_core'):assert marker in SVC,marker
for marker in ('/forecast-overlays','/uncertainty-displays','/calibration-displays','/ensemble-comparisons','/monitoring-overlays','/spatial-temporal-layers','/causal-overlays','/decision-bindings','/snapshots'):assert marker in ROUTER,marker
assert SCHEMA['properties']['contract']['const']=='sc.visual-runtime.predictive-intelligence.v1'
print(f'PASS - dependency-free release contract; migration ledger max=300, 0071 chars={len(migrations[-1][1])}')
print('PASS - v2.67.0 Visual Predictive Intelligence release contract')
