#!/usr/bin/env python3
from pathlib import Path
import ast
ROOT=Path(__file__).resolve().parents[1]
CFG=(ROOT/'backend/app/config.py').read_text(); MIG=(ROOT/'backend/app/migrations.py').read_text(); MOD=(ROOT/'backend/app/models.py').read_text(); MAIN=(ROOT/'backend/app/main.py').read_text(); ROUTER=(ROOT/'backend/app/routers/open_forensics.py').read_text(); SERVICE=(ROOT/'backend/app/services/open_forensics.py').read_text(); WP=(ROOT/'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text(); SDKPY=(ROOT/'backend/public_sdk/python/sc_platform_core_public/client.py').read_text(); SDKJS=(ROOT/'backend/public_sdk/javascript/index.mjs').read_text(); PKG=(ROOT/'backend/public_sdk/javascript/package.json').read_text(); PYPROJECT=(ROOT/'backend/public_sdk/python/pyproject.toml').read_text()
assert 'version: str = "2.46.0"' in CFG and 'SustainableCatalystPlatformCore/2.46.0' in CFG
mod=ast.parse(MIG); migrations=None
for n in mod.body:
    if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MIGRATIONS' for t in n.targets): migrations=ast.literal_eval(n.value)
assert migrations; versions=[v for v,_ in migrations]; descriptions=dict(migrations); assert versions[-1]=='0050' and len(versions)==len(set(versions)); assert len(descriptions['0050'])<=300
for name in ['ForensicPlaceRecord','ForensicEvidenceSpatialBindingRecord','ForensicEventPlaceBindingRecord','ForensicSpatialUncertaintyEnvelopeRecord','ForensicTrajectoryEvidenceRecord','ForensicSpatialTemporalIntersectionRecord','ForensicSpatialTemporalViewRecord','ForensicSpatialTemporalSnapshotRecord']: assert f'class {name}' in MOD
for term in ['forensic_place_registry_by_core','evidence_spatial_binding_by_core','event_place_binding_by_core','spatial_uncertainty_envelopes_by_core','trajectory_evidence_registry_by_core','explicit_spatial_temporal_intersections_by_core','linked_map_timeline_specification_by_core','site_intelligence_handoffs_by_core','immutable_spatial_temporal_snapshots_by_core','crs_reprojection_by_core','spatial_join_by_core','routing_by_core','remote_sensing_by_core','trajectory_interpolation_execution_by_core','automatic_location_truth_determination_by_core']: assert term in SERVICE
for term in ['/places','/spatial-bindings','/place-bindings','/spatial-uncertainty-envelopes','/trajectory-evidence','/spatial-temporal-intersections','/spatial-temporal-views','/spatial-temporal-evidence','/forensic-scene-specification','/site-intelligence-handoff','/spatial-temporal-snapshots']: assert term in ROUTER
assert 'forensic spatial/temporal evidence integration' in MAIN
assert 'Version: 2.46.0' in WP and 'sc_platform_core_forensic_spatial_temporal_status' in WP
assert 'open_forensics_spatial_temporal_evidence' in SDKPY and 'openForensicsSpatialTemporalEvidence' in SDKJS
assert '"version": "2.46.0"' in PKG and 'version = "2.46.0"' in PYPROJECT
print(f"PASS - dependency-free release contract; migration ledger max=300, 0050 chars={len(descriptions['0050'])}")
print('PASS - v2.46.0 Forensic Spatial/Temporal Evidence Integration release contract')
