from pathlib import Path
import ast,sys
root=Path(__file__).resolve().parents[1]
required=[
'backend/app/services/uncertainty_probabilistic_evidence.py','backend/app/routers/uncertainty_probabilistic_evidence.py','backend/tests/test_uncertainty_probabilistic_evidence_v3210.py','backend/scripts/validate_uncertainty_probabilistic_evidence_v3_21_0.py','RELEASE_NOTES_V3210.md','PLATFORM_CORE_V3210_UNCERTAINTY_PROBABILISTIC_EVIDENCE_AUDIT.md']
missing=[x for x in required if not (root/x).exists()]
assert not missing, f'missing v3.21.0 files: {missing}'
for f in ['backend/app/models.py','backend/app/config.py','backend/app/main.py','backend/app/migrations.py','backend/app/services/uncertainty_probabilistic_evidence.py','backend/app/routers/uncertainty_probabilistic_evidence.py']:
    ast.parse((root/f).read_text())
config=(root/'backend/app/config.py').read_text(); mig=(root/'backend/app/migrations.py').read_text(); wp=(root/'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text()
assert 'version: str = "3.21.0"' in config
assert '("0108", "Platform Core v3.21.0 — Uncertainty & Probabilistic Evidence Integration")' in mig
assert 'sc.core.uncertainty-probabilistic-evidence.v1' in (root/'backend/app/services/uncertainty_probabilistic_evidence.py').read_text()
assert 'sc.analytics-r.uncertainty-sensitivity-runtime.v1' in (root/'backend/app/services/uncertainty_probabilistic_evidence.py').read_text()
assert ' * Version: 3.21.0' in wp and "define('SCPC_VERSION', '3.21.0');" in wp
print('PLATFORM_CORE_V3210_RELEASE_CONTRACT=PASS')
