def test_health_and_ready(client):
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["version"] == "2.5.0"

    ready = client.get("/ready")
    assert ready.status_code == 200
    assert ready.json()["database"] == "ready"


def test_meta_declares_deferred_capabilities(client):
    response = client.get("/v1/meta")
    assert response.status_code == 200
    body = response.json()
    assert "universal_entity_registry" in body["capabilities"]
    assert "controlled_predicate_registry" in body["capabilities"]
    assert "public_knowledge_explorer" in body["capabilities"]
    assert "tamper_evident_ledger" in body["capabilities"]
    assert "evidence_manifests" in body["capabilities"]
    assert "unified_public_api_v1" in body["capabilities"]
    assert "developer_portal" in body["capabilities"]
    assert "signed_webhooks" in body["capabilities"]
    assert "public_trust_center" in body["capabilities"]
    assert "machine_readable_trust_status" in body["capabilities"]
    assert "large_scale_graph_database_adapter" in body["deferred_capabilities"]
