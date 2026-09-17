from fastapi.testclient import TestClient
from app.main import create_app

def test_readiness_and_boundaries(tmp_path,monkeypatch):
 monkeypatch.setenv("SC_CORE_DATABASE_URL",f"sqlite:///{tmp_path/'a.db'}");app=create_app();c=TestClient(app);d=c.get("/v1/visual-runtime/unified/readiness").json();assert d["release"]=="2.70.0" and d["migration_0074_applied"] and d["unified_visual_reasoning_workspace_registry_by_core"] is True and d["render_by_core"] is False and d["decision_ranking_by_core"] is False

def test_roundtrip_cross_layer_bundle_and_snapshot(tmp_path,monkeypatch):
 monkeypatch.setenv("SC_CORE_DATABASE_URL",f"sqlite:///{tmp_path/'b.db'}");app=create_app();c=TestClient(app)
 # create a composition using ORM to avoid renderer API setup noise
 from app.models import Entity,VisualRuntimeSceneRecord,VisualViewCompositionRecord
 with app.state.database.session_factory() as db:
  ent=Entity(id="project:v270-roundtrip",entity_type="research-project",slug="v270-roundtrip",name="Unified Test Project",visibility="public");db.add(ent);db.flush()
  scene=VisualRuntimeSceneRecord(project_entity_id=ent.id,scene_key="unified",name="Unified Scene",visibility="public");db.add(scene);db.flush()
  comp=VisualViewCompositionRecord(scene_id=scene.id,composition_key="u",name="Unified",visibility="public");db.add(comp);db.commit();db.refresh(comp);cid=comp.id
 w=c.post(f"/v1/visual-runtime/unified/compositions/{cid}/workspaces",json={"data":{"workspace_key":"research","name":"Unified Research","visibility":"public"}}).json();wid=w["id"]
 b=c.post(f"/v1/visual-runtime/unified/workspaces/{wid}/layer-bindings",json={"data":{"binding_key":"all","predictive_workspace_ids":["p1"],"forensics_workspace_ids":["f1"],"decision_workspace_ids":["d1"]}});assert b.status_code==200
 rp=c.post(f"/v1/visual-runtime/unified/workspaces/{wid}/reasoning-paths",json={"data":{"path_key":"evidence-to-decision","stages":[{"layer":"scene"},{"layer":"query"},{"layer":"model"},{"layer":"predictive"},{"layer":"forensics"},{"layer":"decision"}]}});assert rp.status_code==200
 h=c.post(f"/v1/visual-runtime/unified/workspaces/{wid}/handoffs",json={"data":{"handoff_key":"lab","target_product":"lab","request_contract":{"mode":"external"}}});assert h.status_code==200
 s1=c.post(f"/v1/visual-runtime/unified/workspaces/{wid}/snapshots",json={"data":{}}).json();s2=c.post(f"/v1/visual-runtime/unified/workspaces/{wid}/snapshots",json={"data":{}}).json();assert s2["previous_snapshot_hash"]==s1["content_hash"]
 out=c.get(f"/v1/visual-runtime/unified/workspaces/{wid}/bundle").json();assert out["contract"]=="sc.visual-runtime.unified-reasoning.v1" and len(out["layer_bindings"])==1 and len(out["reasoning_paths"])==1

def test_rejects_core_execution_flags(tmp_path,monkeypatch):
 monkeypatch.setenv("SC_CORE_DATABASE_URL",f"sqlite:///{tmp_path/'c.db'}");app=create_app();c=TestClient(app)
 from app.models import Entity,VisualRuntimeSceneRecord,VisualViewCompositionRecord
 with app.state.database.session_factory() as db:
  ent=Entity(id="project:v270-boundary",entity_type="research-project",slug="v270-boundary",name="Boundary Test Project",visibility="private");db.add(ent);db.flush()
  scene=VisualRuntimeSceneRecord(project_entity_id=ent.id,scene_key="boundary",name="Boundary Scene",visibility="private");db.add(scene);db.flush()
  comp=VisualViewCompositionRecord(scene_id=scene.id,composition_key="x",name="X",visibility="private");db.add(comp);db.commit();db.refresh(comp);cid=comp.id
 r=c.post(f"/v1/visual-runtime/unified/compositions/{cid}/workspaces",json={"data":{"workspace_key":"x","name":"X","model_execution_by_core":True}});assert r.status_code==422
