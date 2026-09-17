#!/usr/bin/env python3
from pathlib import Path
import ast,json
ROOT=Path(__file__).resolve().parents[1]
CFG=(ROOT/'backend/app/config.py').read_text(); MIG=(ROOT/'backend/app/migrations.py').read_text(); MOD=(ROOT/'backend/app/models.py').read_text(); MAIN=(ROOT/'backend/app/main.py').read_text(); ROUTER=(ROOT/'backend/app/routers/open_forensics.py').read_text(); SERVICE=(ROOT/'backend/app/services/open_forensics.py').read_text(); WP=(ROOT/'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text(); SDKPY=(ROOT/'backend/public_sdk/python/sc_platform_core_public/client.py').read_text(); SDKJS=(ROOT/'backend/public_sdk/javascript/index.mjs').read_text(); PKG=(ROOT/'backend/public_sdk/javascript/package.json').read_text(); PYPROJECT=(ROOT/'backend/public_sdk/python/pyproject.toml').read_text()
assert 'version: str = "2.51.0"' in CFG and 'SustainableCatalystPlatformCore/2.51.0' in CFG
mod=ast.parse(MIG); migrations=None
for n in mod.body:
    if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MIGRATIONS' for t in n.targets): migrations=ast.literal_eval(n.value)
assert migrations; versions=[v for v,_ in migrations]; descriptions=dict(migrations); assert versions[-1]=='0055' and len(versions)==len(set(versions)); assert len(descriptions['0055'])<=300
for name in ['ForensicInvestigationPackageRecord','ForensicInvestigationPackageComponentRecord','ForensicInvestigationPackageArtifactRecord','ForensicInvestigationPackageEnvironmentRecord','ForensicInvestigationPackageVerificationRecord','ForensicInvestigationPackageReviewRecord','ForensicInvestigationPackageSnapshotRecord']: assert f'class {name}' in MOD,name
for term in ['reproducible_investigation_packages_by_core','frozen_cross_forensics_component_manifests_by_core','investigation_package_artifact_registry_by_core','investigation_environment_manifest_capture_by_core','investigation_package_integrity_verification_by_core','independent_review_recording_by_core','portable_investigation_review_bundles_by_core','reproducibility_equals_truth_by_core','automatic_package_authenticity_determination_by_core','automatic_package_admissibility_determination_by_core']: assert term in SERVICE,term
for term in ['/reproducible-packages','/artifacts','/environments','/verify','/reviews','/snapshots','/portable']: assert term in ROUTER,term
assert 'reproducible investigation packages' in MAIN.lower()
assert 'Version: 2.51.0' in WP and 'sc_platform_core_reproducible_investigation_packages_status' in WP
assert 'open_forensics_reproducible_investigation_package' in SDKPY and 'openForensicsReproducibleInvestigationPackage' in SDKJS
assert '"version": "2.51.0"' in PKG and 'version = "2.51.0"' in PYPROJECT
assert (ROOT/'backend/public_sdk/downloads/sc-platform-core-public-python-v2.51.0.zip').is_file()
assert (ROOT/'backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.51.0.zip').is_file()
print(f"PASS - dependency-free release contract; migration ledger max=300, 0055 chars={len(descriptions['0055'])}")
print('PASS - v2.51.0 Reproducible Investigation Packages release contract')
