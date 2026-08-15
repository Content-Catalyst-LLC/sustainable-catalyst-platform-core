from __future__ import annotations
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def req(path):
    p=ROOT/path
    if not p.is_file(): raise SystemExit(f"ERROR - required file missing: {path}")
    return p
def contains(path,needle):
    if needle not in req(path).read_text(errors="replace"): raise SystemExit(f"ERROR - {path} missing marker: {needle}")
def main():
    required=[
      "backend/app/config.py","backend/app/models.py","backend/app/services/facilities.py","backend/app/routers/facilities.py","backend/app/routers/meta.py","backend/app/migrations.py","backend/tests/test_operational_facilities_v2100.py","backend/scripts/validate_operational_facilities.py",
      "deployment/platform-core-v2100.env.example","docs/OPERATIONAL_EVIDENCE_FACILITY_REGISTRY_V2100.md","RELEASE_NOTES_V2100.md","PLATFORM_CORE_V2100_INSTALL_AND_TEST.md","PLATFORM_CORE_V2100_OPERATIONAL_FACILITY_AUDIT.md","render.yaml","wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php",
      "backend/public_sdk/downloads/sc-platform-core-public-python-v2.10.0.zip","backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.10.0.zip","schemas/operational-facility-v1.schema.json","schemas/facility-observation-v1.schema.json"]
    for x in required:req(x)
    contains("backend/app/config.py","version: str = \"2.10.0\"")
    contains("backend/app/migrations.py","(\"0013\", \"Operational facility registry")
    for cls in ["OperationalFacility","FacilitySourceIdentifier","FacilityObservation"]: contains("backend/app/models.py",f"class {cls}(Base):")
    contains("backend/app/routers/facilities.py","automatic_conflict_flattening")
    contains("backend/app/routers/meta.py","\"operational_evidence_facility_registry\": \"ready\"")
    contains("wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php","Version: 2.10.0")
    contains("wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php","sc_platform_core_facility_registry_status")
    assert json.loads(req("backend/public_sdk/javascript/package.json").read_text()).get("version")=="2.10.0"
    assert re.search(r"^version\s*=\s*\"2\.10\.0\"\s*$",req("backend/public_sdk/python/pyproject.toml").read_text(),re.M)
    for x in ["schemas/operational-facility-v1.schema.json","schemas/facility-observation-v1.schema.json"]: json.loads(req(x).read_text())
    print("PASS - v2.10.0 release contract")
if __name__=="__main__":main()
