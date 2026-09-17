#!/usr/bin/env python3
from pathlib import Path
import ast
ROOT=Path(__file__).resolve().parents[1]
CFG=(ROOT/'backend/app/config.py').read_text(); MIG=(ROOT/'backend/app/migrations.py').read_text(); MOD=(ROOT/'backend/app/models.py').read_text(); MAIN=(ROOT/'backend/app/main.py').read_text(); ROUTER=(ROOT/'backend/app/routers/open_forensics.py').read_text(); SERVICE=(ROOT/'backend/app/services/open_forensics.py').read_text(); WP=(ROOT/'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text(); SDKPY=(ROOT/'backend/public_sdk/python/sc_platform_core_public/client.py').read_text(); SDKJS=(ROOT/'backend/public_sdk/javascript/index.mjs').read_text(); PKG=(ROOT/'backend/public_sdk/javascript/package.json').read_text(); PYPROJECT=(ROOT/'backend/public_sdk/python/pyproject.toml').read_text()
assert 'version: str = "2.47.0"' in CFG and 'SustainableCatalystPlatformCore/2.47.0' in CFG
mod=ast.parse(MIG); migrations=None
for n in mod.body:
    if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MIGRATIONS' for t in n.targets): migrations=ast.literal_eval(n.value)
assert migrations; versions=[v for v,_ in migrations]; descriptions=dict(migrations); assert versions[-1]=='0051' and len(versions)==len(set(versions)); assert len(descriptions['0051'])<=300
for name in ['ForensicMediaArtifactRecord','ForensicMediaDerivativeRecord','ForensicMediaMetadataRecord','ForensicMediaFingerprintRecord','ForensicMediaSegmentRecord','ForensicMediaComparisonRecord','ForensicMediaProvenanceSnapshotRecord']: assert f'class {name}' in MOD
for term in ['media_artifact_registry_by_core','declared_derivative_lineage_by_core','media_metadata_preservation_by_core','cryptographic_fingerprint_recording_by_core','perceptual_fingerprint_recording_by_core','frame_segment_reference_registry_by_core','provenance_aware_media_comparisons_by_core','immutable_media_provenance_snapshots_by_core','media_decoding_by_core','perceptual_fingerprint_computation_by_core','media_similarity_execution_by_core','derivative_detection_by_core','authenticity_determination_from_media_by_core','manipulation_intent_determination_by_core','media_authorship_attribution_by_core']: assert term in SERVICE
for term in ['/media-artifacts','/media-derivations','/metadata','/fingerprints','/segments','/media-comparisons','/media-provenance','/media-lineage-graph','/media-comparison-bundle','/media-provenance-snapshots']: assert term in ROUTER
assert 'media artifact & derivative provenance' in MAIN
assert 'Version: 2.47.0' in WP and 'sc_platform_core_forensic_media_provenance_status' in WP
assert 'open_forensics_media_provenance' in SDKPY and 'openForensicsMediaProvenance' in SDKJS
assert '"version": "2.47.0"' in PKG and 'version = "2.47.0"' in PYPROJECT
print(f"PASS - dependency-free release contract; migration ledger max=300, 0051 chars={len(descriptions['0051'])}")
print('PASS - v2.47.0 Media Artifact & Derivative Provenance release contract')
