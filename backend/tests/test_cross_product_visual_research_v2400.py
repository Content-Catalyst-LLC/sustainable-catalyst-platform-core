from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.migrations import migration_status
from app.models import Entity


def app_client(tmp_path):
    app = create_app(Settings(database_url=f"sqlite:///{tmp_path/'v2400.db'}", version="2.53.0"))
    return app, TestClient(app)


def seed_project(app):
    with app.state.database.session_factory() as db:
        db.add(Entity(id="project:cross-product", entity_type="research-project", slug="cross-product", name="Cross Product Test", visibility="public"))
        db.commit()


def create_object(client, visibility="public"):
    r = client.post("/v1/cross-product-visual-research", json={"data": {
        "project_entity_id": "project:cross-product", "object_key": f"energy-study-{visibility}",
        "name": "Energy Systems Visual Research Object", "object_kind": "research-composite", "visibility": visibility,
    }})
    assert r.status_code == 200, r.text
    return r.json()["id"]


def test_readiness_health_and_migration_0044(tmp_path):
    app, client = app_client(tmp_path); seed_project(app)
    health = client.get("/health").json()
    assert health["version"] == "2.53.0" and health["cross_product_visual_research_objects"] is True
    ready = client.get("/v1/cross-product-visual-research/readiness").json()
    assert ready["release"] == "2.53.0" and ready["migration_0044_applied"] is True
    assert ready["reference_first_cross_product"] is True and ready["remote_product_fetch_by_core"] is False
    assert ready["model_execution_by_core"] is False and ready["analysis_execution_by_core"] is False
    assert ready["cross_product_truth_merging_by_core"] is False and ready["renderer_execution_by_core"] is False
    assert ready["automatic_truth_promotion"] is False
    assert migration_status(app.state.database)["pending"] == []


def test_cross_product_members_relations_views_portability_and_snapshot(tmp_path):
    app, client = app_client(tmp_path); seed_project(app); oid = create_object(client)
    core = client.post(f"/v1/cross-product-visual-research/{oid}/members", json={"data": {
        "member_key": "research-question", "member_kind": "research-object", "source_product": "platform-core",
        "semantic_role": "question", "label": "Energy transition research question", "local_entity_id": "project:cross-product",
    }})
    assert core.status_code == 200, core.text; core_id = core.json()["id"]
    lab = client.post(f"/v1/cross-product-visual-research/{oid}/members", json={"data": {
        "member_key": "lab-study", "member_kind": "result", "source_product": "lab", "semantic_role": "analysis",
        "label": "Lab sensitivity study", "source_ref": {"artifact_id": "lab:study:42", "version": "0.103.0"},
        "external_ref": "sc://lab/studies/42",
    }})
    assert lab.status_code == 200, lab.text; lab_id = lab.json()["id"]
    site = client.post(f"/v1/cross-product-visual-research/{oid}/members", json={"data": {
        "member_key": "site-layer", "member_kind": "spatial-temporal", "source_product": "site-intelligence", "semantic_role": "spatial-context",
        "label": "Grid and infrastructure context", "source_ref": {"scene_id": "scene:energy:1"},
    }})
    assert site.status_code == 200, site.text; site_id = site.json()["id"]
    r1 = client.post(f"/v1/cross-product-visual-research/{oid}/relations", json={"data": {
        "relation_key": "question-to-analysis", "source_member_id": core_id, "target_member_id": lab_id, "relation_kind": "informs",
    }})
    assert r1.status_code == 200, r1.text
    r2 = client.post(f"/v1/cross-product-visual-research/{oid}/relations", json={"data": {
        "relation_key": "spatializes-analysis", "source_member_id": site_id, "target_member_id": lab_id, "relation_kind": "spatializes",
    }})
    assert r2.status_code == 200, r2.text
    view = client.post(f"/v1/cross-product-visual-research/{oid}/views", json={"data": {
        "view_key": "overview", "name": "Cross-Product Overview", "view_kind": "composite",
        "member_order": [core_id, lab_id, site_id], "renderer_contract": "contract.d3",
    }})
    assert view.status_code == 200, view.text
    valid = client.get(f"/v1/cross-product-visual-research/{oid}/validate").json()
    assert valid["valid"] is True and valid["cross_product"] is True and len(valid["source_products"]) == 3
    spec = client.get(f"/v1/cross-product-visual-research/{oid}/visualization", params={"view_id": view.json()["id"]}).json()
    assert spec["contract"] == "sc.cross-product-visual-research-object.v1"
    assert spec["composition"]["preserve_source_product_identity"] is True and spec["renderer_neutral"] is True
    assert spec["layout_execution_by_core"] is False and spec["renderer_execution_by_core"] is False
    portable = client.get(f"/v1/cross-product-visual-research/{oid}/portable-package").json()
    assert portable["portable"] is True and portable["reference_first"] is True and portable["embedded_remote_content"] is False
    first = client.post(f"/v1/cross-product-visual-research/{oid}/snapshots", json={"data": {"created_by": "test"}}).json()
    second = client.post(f"/v1/cross-product-visual-research/{oid}/snapshots", json={"data": {"created_by": "test"}}).json()
    assert first["revision"] == 1 and second["revision"] == 2 and first["content_hash"] == second["content_hash"] and len(first["content_hash"]) == 64


def test_reference_guards_and_runtime_boundary(tmp_path):
    app, client = app_client(tmp_path); seed_project(app); oid = create_object(client)
    missing_remote_ref = client.post(f"/v1/cross-product-visual-research/{oid}/members", json={"data": {
        "member_key": "bad", "member_kind": "result", "source_product": "workbench", "label": "Missing explicit reference",
    }})
    assert missing_remote_ref.status_code == 422
    core = client.post(f"/v1/cross-product-visual-research/{oid}/members", json={"data": {
        "member_key": "core", "member_kind": "research-object", "source_product": "platform-core", "label": "Core project", "local_entity_id": "project:cross-product",
    }}).json()
    self_relation = client.post(f"/v1/cross-product-visual-research/{oid}/relations", json={"data": {
        "relation_key": "self", "source_member_id": core["id"], "target_member_id": core["id"], "relation_kind": "relates-to",
    }})
    assert self_relation.status_code == 422
    handoff = client.post(f"/v1/cross-product-visual-research/{oid}/runtime-handoff", json={"data": {"target_product": "lab", "operation": "inspect-and-analyze"}})
    assert handoff.status_code == 200, handoff.text
    data = handoff.json(); assert data["model_execution_by_core"] is False and data["analysis_execution_by_core"] is False and data["cross_product_truth_merging_by_core"] is False
    denied = client.post(f"/v1/cross-product-visual-research/{oid}/runtime-handoff", json={"data": {"target_product": "lab", "execute_by_core": True}})
    assert denied.status_code == 422
