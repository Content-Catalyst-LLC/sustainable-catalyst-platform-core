from __future__ import annotations
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def req(path):
    p=ROOT/path
    if not p.is_file(): raise SystemExit(f'ERROR - required file missing: {path}')
    return p
def contains(path,needle):
    if needle not in req(path).read_text(errors='replace'): raise SystemExit(f'ERROR - {path} missing marker: {needle}')
def main():
    required=[
      'backend/app/config.py','backend/app/models.py','backend/app/services/scientific_service_fabric.py','backend/app/routers/scientific_service_fabric.py','backend/app/routers/meta.py','backend/app/migrations.py','backend/tests/test_scientific_service_fabric_v2130.py','backend/scripts/validate_scientific_service_fabric.py',
      'deployment/platform-core-v2130.env.example','docs/EARTH_OCEAN_SPACE_SCIENTIFIC_SERVICE_FABRIC_V2130.md','RELEASE_NOTES_V2130.md','PLATFORM_CORE_V2130_INSTALL_AND_TEST.md','PLATFORM_CORE_V2130_SCIENTIFIC_SERVICE_FABRIC_AUDIT.md','render.yaml','wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php',
      'backend/public_sdk/downloads/sc-platform-core-public-python-v2.13.0.zip','backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.13.0.zip','schemas/scientific-domain-binding-v1.schema.json']
    for x in required:req(x)
    contains('backend/app/config.py','version: str = "2.13.0"')
    contains('backend/app/migrations.py','("0016", "Earth, ocean, space')
    contains('backend/app/models.py','class ScientificDomainBinding(Base):')
    contains('backend/app/services/scientific_service_fabric.py','truth_precedence="none"')
    contains('backend/app/routers/scientific_service_fabric.py','automatic_cross_domain_blending')
    contains('backend/app/routers/meta.py','"earth_ocean_space_scientific_service_fabric"')
    contains('wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php','Version: 2.13.0')
    contains('wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php','sc_platform_core_scientific_fabric_status')
    assert json.loads(req('backend/public_sdk/javascript/package.json').read_text()).get('version')=='2.13.0'
    assert re.search(r'^version\s*=\s*"2\.13\.0"\s*$',req('backend/public_sdk/python/pyproject.toml').read_text(),re.M)
    json.loads(req('schemas/scientific-domain-binding-v1.schema.json').read_text())
    print('PASS - v2.13.0 release contract')
if __name__=='__main__':main()
