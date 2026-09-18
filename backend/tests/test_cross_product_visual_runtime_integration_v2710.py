from fastapi.testclient import TestClient
from app.main import create_app


def _workspace(app, key="x", visibility="public"):
    from app.models import Entity, VisualRuntimeSceneRecord, VisualViewCompositionRecord, UnifiedVisualReasoningWorkspaceRecord
    with app.state.database.session_factory() as db:
        ent=Entity(id=f"project:v271-{key}",entity_type="research-project",slug=f"v271-{key}",name="v271 project",visibility=visibility);db.add(ent);db.flush()
        scene=VisualRuntimeSceneRecord(project_entity_id=ent.id,scene_key=key,name="scene",visibility=visibility);db.add(scene);db.flush()
        comp=VisualViewCompositionRecord(scene_id=scene.id,composition_key=key,name="composition",visibility=visibility);db.add(comp);db.flush()
        ws=UnifiedVisualReasoningWorkspaceRecord(composition_id=comp.id,workspace_key=key,name="workspace",visibility=visibility);db.add(ws);db.commit();db.refresh(ws);return ws.id


def test_readiness_products_and_boundaries(tmp_path, monkeypatch):
    monkeypatch.setenv("SC_CORE_DATABASE_URL",f"sqlite:///{tmp_path/'a.db'}"); app=create_app(); c=TestClient(app)
    d=c.get("/v1/visual-runtime/integrations/readiness").json()
    assert d["release"]=="2.71.0" and d["migration_0075_applied"] is True
    assert set(d["products"])=={"library","lab","workbench","decision-studio","site-intelligence","workspace","research-librarian"}
    assert d["product_integration_registry_by_core"] is True and d["render_by_core"] is False and d["compute_by_core"] is False and d["automatic_cross_product_sync"] is False


def test_cross_product_roundtrip_and_snapshot(tmp_path, monkeypatch):
    monkeypatch.setenv("SC_CORE_DATABASE_URL",f"sqlite:///{tmp_path/'b.db'}"); app=create_app(); c=TestClient(app); wid=_workspace(app,"roundtrip")
    r=c.post(f"/v1/visual-runtime/integrations/workspaces/{wid}/products",json={"data":{"product_key":"library","integration_key":"library-main","name":"Library Visual Runtime","runtime_contract":{"mode":"reference-first"}}}); assert r.status_code==200, r.text; iid=r.json()["id"]
    assert c.post(f"/v1/visual-runtime/integrations/integrations/{iid}/object-bindings",json={"data":{"binding_key":"doc","canonical_object_refs":["research:1"],"product_object_refs":["library:doc:1"],"semantic_roles":["source-document"]}}).status_code==200
    assert c.post(f"/v1/visual-runtime/integrations/integrations/{iid}/context-bindings",json={"data":{"context_key":"project","context_type":"research-project","canonical_context_ref":"project:1"}}).status_code==200
    assert c.post(f"/v1/visual-runtime/integrations/integrations/{iid}/capabilities",json={"data":{"capability_key":"document","object_kinds":["document"]}}).status_code==200
    assert c.post(f"/v1/visual-runtime/integrations/integrations/{iid}/view-bindings",json={"data":{"binding_key":"views","unified_view_ids":[],"product_view_refs":["library:view:1"]}}).status_code==200
    assert c.post(f"/v1/visual-runtime/integrations/workspaces/{wid}/handoff-routes",json={"data":{"route_key":"library-to-lab","source_product":"library","target_product":"lab","capability_key":"plot","request_contract":{"external":True}}}).status_code==200
    assert c.post(f"/v1/visual-runtime/integrations/workspaces/{wid}/sync-records",json={"data":{"sync_key":"library-workspace","source_product":"library","target_product":"workspace","state_hashes":{"source":"abc"},"synchronization_evidence":{"declared":True}}}).status_code==200
    s1=c.post(f"/v1/visual-runtime/integrations/workspaces/{wid}/snapshots",json={"data":{}}).json(); s2=c.post(f"/v1/visual-runtime/integrations/workspaces/{wid}/snapshots",json={"data":{}}).json(); assert s2["previous_snapshot_hash"]==s1["content_hash"]
    b=c.get(f"/v1/visual-runtime/integrations/workspaces/{wid}/bundle").json(); assert b["contract"]=="sc.visual-runtime.cross-product-integration.v1" and len(b["integrations"])==1 and len(b["handoff_routes"])==1 and len(b["sync_records"])==1


def test_rejects_unsupported_product_and_core_execution(tmp_path, monkeypatch):
    monkeypatch.setenv("SC_CORE_DATABASE_URL",f"sqlite:///{tmp_path/'c.db'}"); app=create_app(); c=TestClient(app); wid=_workspace(app,"boundary","private")
    bad=c.post(f"/v1/visual-runtime/integrations/workspaces/{wid}/products",json={"data":{"product_key":"unknown","integration_key":"x","name":"x"}}); assert bad.status_code==422
    bad=c.post(f"/v1/visual-runtime/integrations/workspaces/{wid}/products",json={"data":{"product_key":"lab","integration_key":"x","name":"x","compute_by_core":True}}); assert bad.status_code==422
