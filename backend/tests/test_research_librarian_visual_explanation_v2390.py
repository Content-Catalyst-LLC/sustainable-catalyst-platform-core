from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.migrations import migration_status
from app.models import Entity


def app_client(tmp_path):
    app = create_app(Settings(database_url=f"sqlite:///{tmp_path/'v2390.db'}", version="2.51.0"))
    return app, TestClient(app)


def seed_project(app):
    with app.state.database.session_factory() as db:
        db.add(Entity(id="project:explain", entity_type="research-project", slug="explain", name="Explanation Test", visibility="public")); db.commit()


def make_explanation(client, visibility="public"):
    response = client.post("/v1/research-visual-explanations", json={"data": {
        "project_entity_id": "project:explain", "explanation_key": f"ex-{visibility}",
        "name": "Evidence explanation", "question": "What supports the finding?",
        "explanation_kind": "evidence-map", "visibility": visibility,
    }})
    assert response.status_code == 200, response.text
    return response.json()["id"]


def test_readiness_health_and_migration_0043(tmp_path):
    app, client = app_client(tmp_path); seed_project(app)
    health = client.get("/health").json(); assert health["version"] == "2.51.0"; assert health["research_librarian_visual_explanation"] is True
    ready = client.get("/v1/research-visual-explanations/readiness").json()
    assert ready["release"] == "2.51.0"; assert ready["migration_0043_applied"] is True
    assert ready["source_retrieval_by_core"] is False and ready["natural_language_generation_by_core"] is False
    assert ready["citation_selection_by_core"] is False and ready["source_ranking_by_core"] is False
    assert ready["renderer_execution_by_core"] is False and ready["automatic_truth_promotion"] is False
    assert migration_status(app.state.database)["pending"] == []


def test_explanation_graph_citations_visualization_and_bundle(tmp_path):
    app, client = app_client(tmp_path); seed_project(app); eid = make_explanation(client)
    claim = client.post(f"/v1/research-visual-explanations/{eid}/nodes", json={"data": {
        "node_key": "claim", "node_kind": "claim", "label": "Observed outcome changed", "citation_required": True,
    }}); assert claim.status_code == 200; claim_id = claim.json()["id"]
    source = client.post(f"/v1/research-visual-explanations/{eid}/nodes", json={"data": {
        "node_key": "source", "node_kind": "source", "label": "Primary study",
    }}); assert source.status_code == 200; source_id = source.json()["id"]
    relation = client.post(f"/v1/research-visual-explanations/{eid}/relations", json={"data": {
        "relation_key": "source-supports-claim", "source_node_id": source_id, "target_node_id": claim_id, "relation_kind": "supports", "strength": 0.9,
    }}); assert relation.status_code == 200
    coverage_before = client.get(f"/v1/research-visual-explanations/{eid}/citation-coverage").json(); assert coverage_before["coverage_complete"] is False
    citation = client.post(f"/v1/research-visual-explanations/{eid}/citations", json={"data": {
        "citation_key": "study-1", "node_id": claim_id, "external_uri": "https://example.org/study", "citation_label": "Study 1", "locator": {"page": 4, "figure": "2"},
    }}); assert citation.status_code == 200
    view = client.post(f"/v1/research-visual-explanations/{eid}/views", json={"data": {
        "view_key": "evidence", "name": "Evidence Map", "view_kind": "evidence-map", "focus_node_ids": [claim_id], "renderer_contract": "contract.d3",
    }}); assert view.status_code == 200
    spec = client.get(f"/v1/research-visual-explanations/{eid}/visualization", params={"view_id": view.json()["id"]}).json()
    assert spec["contract"] == "sc.research-librarian-visual-explanation.v1"
    assert spec["coverage"]["coverage_complete"] is True and len(spec["nodes"]) == 2 and len(spec["relations"]) == 1 and len(spec["citations"]) == 1
    assert spec["renderer_neutral"] is True and spec["layout_execution_by_core"] is False and spec["renderer_execution_by_core"] is False
    bundle = client.get(f"/v1/research-visual-explanations/{eid}/bundle").json()
    assert bundle["coverage"]["coverage_complete"] is True; assert bundle["boundaries"]["citation_selection_by_core"] is False


def test_citation_guard_and_relation_guard(tmp_path):
    app, client = app_client(tmp_path); seed_project(app); eid = make_explanation(client)
    node = client.post(f"/v1/research-visual-explanations/{eid}/nodes", json={"data": {"node_key": "claim", "node_kind": "claim", "label": "Claim"}}).json()
    missing_source = client.post(f"/v1/research-visual-explanations/{eid}/citations", json={"data": {"citation_key": "bad", "node_id": node["id"], "locator": {"page": 1}}})
    assert missing_source.status_code == 422
    missing_locator = client.post(f"/v1/research-visual-explanations/{eid}/citations", json={"data": {"citation_key": "bad2", "node_id": node["id"], "external_uri": "https://example.org"}})
    assert missing_locator.status_code == 422
    self_relation = client.post(f"/v1/research-visual-explanations/{eid}/relations", json={"data": {"relation_key": "self", "source_node_id": node["id"], "target_node_id": node["id"], "relation_kind": "supports"}})
    assert self_relation.status_code == 422


def test_snapshots_and_handoff_boundaries(tmp_path):
    app, client = app_client(tmp_path); seed_project(app); eid = make_explanation(client)
    client.post(f"/v1/research-visual-explanations/{eid}/nodes", json={"data": {"node_key": "context", "node_kind": "context", "label": "Context"}})
    first = client.post(f"/v1/research-visual-explanations/{eid}/snapshots", json={"data": {"created_by": "test"}}); assert first.status_code == 200; assert first.json()["revision"] == 1; assert len(first.json()["content_hash"]) == 64
    second = client.post(f"/v1/research-visual-explanations/{eid}/snapshots", json={"data": {"created_by": "test"}}); assert second.status_code == 200; assert second.json()["revision"] == 2; assert second.json()["content_hash"] == first.json()["content_hash"]
    handoff = client.post(f"/v1/research-visual-explanations/{eid}/runtime-handoff", json={"data": {"target_product": "research-librarian", "operation": "evidence-synthesis"}}); assert handoff.status_code == 200
    data = handoff.json(); assert data["source_retrieval_by_core"] is False and data["natural_language_generation_by_core"] is False and data["model_execution_by_core"] is False
    denied = client.post(f"/v1/research-visual-explanations/{eid}/runtime-handoff", json={"data": {"execute_by_core": True}}); assert denied.status_code == 422
