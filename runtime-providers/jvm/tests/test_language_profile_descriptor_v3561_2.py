from fastapi.testclient import TestClient
from app.server import app


def test_live_language_profile_descriptor():
    r=TestClient(app).get("/v1/language-profiles")
    assert r.status_code==200
    p=r.json()
    assert p["runtime_id"]=="sc-runtime-jvm"
    assert p["provider_version"]=="1.0.0"
    assert [x["language"] for x in p["profiles"]]==["java","kotlin","scala"]
    assert [x["language_version"] for x in p["profiles"]]==["21","2.4.20","3.9.0"]
    assert p["explicit_profile_binding_required"] is True
    assert p["autonomous_profile_selection"] is False
    assert p["arbitrary_source"] is False
    assert p["runtime_package_install"] is False
