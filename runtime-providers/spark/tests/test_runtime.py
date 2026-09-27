from fastapi.testclient import TestClient
from app.server import app, _adapter, _master
client=TestClient(app)

def test_health_contract_without_native_session():
    r=client.get("/health"); assert r.status_code==200; d=r.json(); assert d["runtime_id"]=="sc-runtime-spark"; assert d["version"]=="1.0.0"; assert d["spark_version_target"]=="4.2.0"; assert d["scala_binary_version"]=="2.13"

def test_adapter_security_boundaries():
    d=_adapter(); assert d["endpoint"]=="http://127.0.0.1:18106"; assert all(v is False for v in d["boundaries"].values())

def test_capabilities_endpoint():
    r=client.get("/v1/capabilities"); assert r.status_code==200; d=r.json(); assert "distributed_sum" in d["operations"]; assert d["limits"]["max_partitions"]==8

def test_unknown_operation_rejected_before_spark_start():
    r=client.post("/v1/execute",json={"operation":"arbitrary_sql"}); assert r.status_code==400

def test_remote_master_rejected(monkeypatch):
    monkeypatch.setenv("SC_SPARK_MASTER","spark://example:7077")
    try: _master(); assert False
    except RuntimeError: pass
