from fastapi.testclient import TestClient
from app.main import create_app
from app.migrations import migration_status
def test_readiness_and_boundaries(tmp_path,monkeypatch):
 monkeypatch.setenv('SC_CORE_DATABASE_URL',f"sqlite:///{tmp_path/'a.db'}");app=create_app();c=TestClient(app);d=c.get('/v1/visual-runtime/forensics/readiness').json();assert d['release']=='2.68.0' and d['migration_0072_applied'] and d['evidence_authentication_by_core'] is False and d['guilt_inference_by_core'] is False
def test_contract_is_registered():
 from app.services.visual_forensics_workbench import CONTRACT,boundaries
 assert CONTRACT=='sc.visual-runtime.forensics-workbench.v1';assert boundaries()['visual_forensic_workspace_registry_by_core'] is True
