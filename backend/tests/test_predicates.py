def test_default_predicates_are_seeded(client):
    response = client.get("/v1/predicates")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 20
    ids = {item["id"] for item in body["items"]}
    assert {"about", "uses", "measured_by", "related_to"}.issubset(ids)

def test_unregistered_predicate_is_rejected(client, write_headers):
    for slug in ("one", "two"):
        response = client.post("/v1/entities", headers=write_headers, json={"entity_type":"concept","slug":slug,"name":slug.title(),"metadata":{},"aliases":[]})
        assert response.status_code == 201
    response = client.post("/v1/relationships", headers=write_headers, json={"subject_id":"sc:concept:one","predicate":"invented_predicate","object_id":"sc:concept:two","confidence":1.0,"status":"proposed","provenance":{}})
    assert response.status_code == 404

def test_predicate_type_constraint_is_enforced(client, write_headers):
    article = client.post("/v1/entities", headers=write_headers, json={"entity_type":"article","slug":"test-article","name":"Test Article","metadata":{},"aliases":[]}).json()["id"]
    tool = client.post("/v1/entities", headers=write_headers, json={"entity_type":"tool","slug":"test-tool","name":"Test Tool","metadata":{},"aliases":[]}).json()["id"]
    response = client.post("/v1/relationships", headers=write_headers, json={"subject_id":tool,"predicate":"about","object_id":article,"confidence":1.0,"status":"proposed","provenance":{}})
    assert response.status_code == 422
