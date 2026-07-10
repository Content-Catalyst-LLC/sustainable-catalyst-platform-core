def make_entity(client, headers, entity_type, slug, name):
    response = client.post(
        "/v1/entities",
        headers=headers,
        json={
            "entity_type": entity_type,
            "slug": slug,
            "name": name,
            "metadata": {},
            "aliases": [],
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_relationship_and_graph_traversal(client, write_headers):
    article = make_entity(
        client, write_headers, "article", "freshwater-change", "Freshwater Change"
    )
    concept = make_entity(
        client, write_headers, "concept", "freshwater-change", "Freshwater Change Concept"
    )
    indicator = make_entity(
        client, write_headers, "indicator", "water-stress", "Water Stress"
    )

    for payload in [
        {
            "subject_id": article,
            "predicate": "about",
            "object_id": concept,
            "confidence": 1.0,
            "status": "verified",
            "provenance": {},
        },
        {
            "subject_id": concept,
            "predicate": "measured_by",
            "object_id": indicator,
            "confidence": 0.9,
            "status": "verified",
            "provenance": {},
        },
    ]:
        response = client.post(
            "/v1/relationships",
            headers=write_headers,
            json=payload,
        )
        assert response.status_code == 201

    graph = client.get(
        f"/v1/graph/{article}",
        params={"depth": 2, "direction": "outbound"},
    )
    assert graph.status_code == 200
    body = graph.json()
    ids = {node["entity"]["id"] for node in body["nodes"]}
    assert {article, concept, indicator}.issubset(ids)
    assert len(body["edges"]) == 2
