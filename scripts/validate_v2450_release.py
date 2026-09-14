#!/usr/bin/env python3
from pathlib import Path
import ast
ROOT=Path(__file__).resolve().parents[1]
CFG=(ROOT/'backend/app/config.py').read_text(); MIG=(ROOT/'backend/app/migrations.py').read_text(); MOD=(ROOT/'backend/app/models.py').read_text(); MAIN=(ROOT/'backend/app/main.py').read_text(); ROUTER=(ROOT/'backend/app/routers/open_forensics.py').read_text(); SERVICE=(ROOT/'backend/app/services/open_forensics.py').read_text(); WP=(ROOT/'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text(); SDKPY=(ROOT/'backend/public_sdk/python/sc_platform_core_public/client.py').read_text(); SDKJS=(ROOT/'backend/public_sdk/javascript/index.mjs').read_text(); PKG=(ROOT/'backend/public_sdk/javascript/package.json').read_text(); PYPROJECT=(ROOT/'backend/public_sdk/python/pyproject.toml').read_text()
assert 'version: str = "2.45.0"' in CFG and 'SustainableCatalystPlatformCore/2.45.0' in CFG
mod=ast.parse(MIG); migrations=None
for n in mod.body:
    if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MIGRATIONS' for t in n.targets): migrations=ast.literal_eval(n.value)
assert migrations; versions=[v for v,_ in migrations]; descriptions=dict(migrations); assert versions[-1]=='0049' and len(versions)==len(set(versions)); assert len(descriptions['0049'])<=300
for name in ['ForensicEventRecord','ForensicEventEvidenceBindingRecord','ForensicEventParticipantRecord','ForensicEventRelationRecord','ForensicEventReconstructionRecord','ForensicTimelineViewRecord','ForensicTimelineSnapshotRecord']: assert f'class {name}' in MOD
for term in ['forensic_event_registry_by_core','bounded_temporal_assertion_capture_by_core','event_evidence_binding_by_core','explicit_event_relation_registry_by_core','reconstruction_hypothesis_registry_by_core','renderer_neutral_timeline_specification_by_core','immutable_timeline_snapshots_by_core','automatic_event_inference_by_core','automatic_timestamp_inference_by_core','automatic_sequence_truth_determination_by_core','automatic_participant_identity_resolution_by_core']: assert term in SERVICE
for term in ['/events','/evidence-bindings','/participants','/event-relations','/event-reconstructions','/timeline-views','/timeline','/timeline-specification','/timeline-snapshots']: assert term in ROUTER
assert 'forensic timeline and event reconstruction' in MAIN
assert 'Version: 2.45.0' in WP and 'sc_platform_core_forensic_timeline_status' in WP
assert 'open_forensics_timeline' in SDKPY and 'openForensicsTimeline' in SDKJS
assert '"version": "2.45.0"' in PKG and 'version = "2.45.0"' in PYPROJECT
print(f"PASS - dependency-free release contract; migration ledger max=300, 0049 chars={len(descriptions['0049'])}")
print('PASS - v2.45.0 Forensic Timeline & Event Reconstruction release contract')
