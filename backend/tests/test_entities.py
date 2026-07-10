ENTITY = {
    "entity_type": "concept",
    "slug": "planetary-boundaries",
    "name": "Planetary Boundaries",
    "description": "Earth-system boundary framework.",
    "status": "active",
    "visibility": "public",
    "schema_version": "1.0",
    "metadata": {"domain": "sustainability"},
    "aliases": [
        {"namespace": "wikidata", "value": "Q7133917"}
    ]
}


def test_write_requires_key(client):
    response = client.post("/v1/entities", json=ENTITY)
    assert response.status_code == 401


def test_create_get_list_and_resolve_entity(client, write_headers):
    created = client.post(
        "/v1/entities",
        json=ENTITY,
        headers=write_headers,
    )
    assert created.status_code == 201
    body = created.json()
    assert body["id"] == "sc:concept:planetary-boundaries"
    assert body["metadata"]["domain"] == "sustainability"
    assert "metadata_json" not in body

    fetched = client.get("/v1/entities/sc:concept:planetary-boundaries")
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "Planetary Boundaries"

    listed = client.get("/v1/entities", params={"entity_type": "concept"})
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    resolved = client.get(
        "/v1/entities/resolve",
        params={"namespace": "wikidata", "value": "Q7133917"},
    )
    assert resolved.status_code == 200
    assert resolved.json()["id"] == "sc:concept:planetary-boundaries"


def test_rejects_inconsistent_id(client, write_headers):
    payload = {**ENTITY, "id": "sc:concept:wrong-slug"}
    response = client.post(
        "/v1/entities",
        json=payload,
        headers=write_headers,
    )
    assert response.status_code == 422
