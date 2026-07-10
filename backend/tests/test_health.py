def test_health_and_ready(client):
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["version"] == "2.1.0"

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
    assert "full_evidence_ledger" in body["deferred_capabilities"]
