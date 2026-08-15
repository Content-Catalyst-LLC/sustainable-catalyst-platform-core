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
      'backend/app/config.py','backend/app/models.py','backend/app/services/cross_product_exchange.py','backend/app/routers/cross_product_exchange.py','backend/app/routers/meta.py','backend/app/migrations.py','backend/tests/test_cross_product_exchange_v2140.py','backend/scripts/validate_cross_product_exchange.py',
      'deployment/platform-core-v2140.env.example','docs/CROSS_PRODUCT_EVIDENCE_EXCHANGE_V2140.md','RELEASE_NOTES_V2140.md','PLATFORM_CORE_V2140_INSTALL_AND_TEST.md','PLATFORM_CORE_V2140_CROSS_PRODUCT_EXCHANGE_AUDIT.md','render.yaml','wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php',
      'backend/public_sdk/downloads/sc-platform-core-public-python-v2.14.0.zip','backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.14.0.zip','schemas/cross-product-exchange-package-v1.schema.json']
    for x in required:req(x)
    contains('backend/app/config.py','version: str = "2.14.0"')
    contains('backend/app/config.py','cross_product_exchange_enabled: bool = True')
    contains('backend/app/migrations.py','("0017", "Cross-product evidence exchange')
    contains('backend/app/models.py','class CrossProductExchangePackage(Base):')
    contains('backend/app/models.py','class CrossProductExchangeReceipt(Base):')
    contains('backend/app/services/cross_product_exchange.py','"reference_first": True')
    contains('backend/app/services/cross_product_exchange.py','"automatic_truth_promotion": False')
    contains('backend/app/services/cross_product_exchange.py','"automatic_cross_product_delivery": False')
    contains('backend/app/routers/meta.py','"cross_product_evidence_exchange"')
    contains('wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php','Version: 2.14.0')
    contains('wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php','sc_platform_core_exchange_status')
    assert json.loads(req('backend/public_sdk/javascript/package.json').read_text()).get('version')=='2.14.0'
    assert re.search(r'^version\s*=\s*"2\.14\.0"\s*$',req('backend/public_sdk/python/pyproject.toml').read_text(),re.M)
    json.loads(req('schemas/cross-product-exchange-package-v1.schema.json').read_text())
    print('PASS - v2.14.0 release contract')
if __name__=='__main__':main()
