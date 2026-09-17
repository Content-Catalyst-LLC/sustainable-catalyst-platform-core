from fastapi.testclient import TestClient
from app.main import create_app
def test_readiness_and_boundaries(tmp_path,monkeypatch):
 monkeypatch.setenv("SC_CORE_DATABASE_URL",f"sqlite:///{tmp_path/'a.db'}");app=create_app();c=TestClient(app);d=c.get("/v1/visual-runtime/decision/readiness").json();assert d["release"]=="2.69.0" and d["migration_0073_applied"] and d["option_ranking_by_core"] is False and d["decision_execution_by_core"] is False
def test_contract_is_registered():
 from app.services.visual_decision_intelligence import CONTRACT,boundaries
 assert CONTRACT=="sc.visual-runtime.decision-intelligence.v1";assert boundaries()["visual_decision_workspace_registry_by_core"] is True
