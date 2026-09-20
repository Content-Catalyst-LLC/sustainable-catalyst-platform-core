from pathlib import Path
R=Path(__file__).resolve().parents[2]
s=(R/'backend/app/services/reproducible_research.py').read_text()
assert "CONTRACT='sc.research.reproducible-package.v1'" in s
for x in ('package_registry_by_core','component_manifest_by_core','artifact_registry_by_core','environment_capture_by_core','replay_plan_registry_by_core','verification_evidence_registry_by_core','review_registry_by_core','immutable_package_snapshots_by_core'): assert x in s
for x in ('execute_replay_by_core','reproduce_analysis_by_core','validate_finding_by_core','certify_scientific_truth_by_core'): assert x in s
print('PASS - Platform Core v2.75.0 Reproducible Research Package Runtime invariants')
