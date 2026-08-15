from __future__ import annotations
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def req(path):
    p=ROOT/path
    if not p.is_file(): raise SystemExit(f"ERROR - required file missing: {path}")
    return p
def contains(path,needle):
    if needle not in req(path).read_text(errors='replace'): raise SystemExit(f"ERROR - {path} missing marker: {needle}")
def main():
    required=[
      'backend/app/config.py','backend/app/models.py','backend/app/services/country_evidence.py','backend/app/routers/country_evidence.py','backend/app/routers/meta.py','backend/app/migrations.py','backend/tests/test_country_evidence_federation_v2120.py','backend/scripts/validate_country_evidence.py',
      'deployment/platform-core-v2120.env.example','docs/COUNTRY_EVIDENCE_FEDERATION_RECONCILIATION_V2120.md','RELEASE_NOTES_V2120.md','PLATFORM_CORE_V2120_INSTALL_AND_TEST.md','PLATFORM_CORE_V2120_COUNTRY_EVIDENCE_AUDIT.md','render.yaml','wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php',
      'backend/public_sdk/downloads/sc-platform-core-public-python-v2.12.0.zip','backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.12.0.zip','schemas/country-evidence-reconciliation-v1.schema.json']
    for x in required:req(x)
    contains('backend/app/config.py','version: str = "2.12.0"')
    contains('backend/app/migrations.py','("0015", "Country evidence federation and reconciliation')
    contains('backend/app/models.py','class CountryEvidenceReconciliation(Base):')
    contains('backend/app/services/country_evidence.py','automatic_averaging')
    contains('backend/app/services/country_evidence.py','subnational_scope_never_substitutes_for_national_scope')
    contains('backend/app/routers/country_evidence.py','knowledge_context_truth_precedence')
    contains('backend/app/routers/meta.py','"country_evidence_federation_reconciliation"')
    contains('wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php','Version: 2.12.0')
    contains('wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php','sc_platform_core_country_evidence_status')
    assert json.loads(req('backend/public_sdk/javascript/package.json').read_text()).get('version')=='2.12.0'
    assert re.search(r'^version\s*=\s*"2\.12\.0"\s*$',req('backend/public_sdk/python/pyproject.toml').read_text(),re.M)
    json.loads(req('schemas/country-evidence-reconciliation-v1.schema.json').read_text())
    print('PASS - v2.12.0 release contract')
if __name__=='__main__':main()
