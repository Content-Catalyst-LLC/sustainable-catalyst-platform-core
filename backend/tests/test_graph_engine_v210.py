def create_entity(client, headers, entity_type, slug, name):
    response = client.post("/v1/entities", headers=headers, json={"entity_type":entity_type,"slug":slug,"name":name,"metadata":{},"aliases":[]})
    assert response.status_code == 201
    return response.json()["id"]

def create_relationship(client, headers, subject, predicate, object_id, status="verified"):
    response = client.post("/v1/relationships", headers=headers, json={"subject_id":subject,"predicate":predicate,"object_id":object_id,"confidence":0.95,"status":status,"provenance":{"test":True}})
    assert response.status_code == 201
    return response.json()

def test_path_neighborhood_recommendations_jsonld_and_review(client, write_headers):
    article=create_entity(client,write_headers,"article","water-article","Water Article")
    concept=create_entity(client,write_headers,"concept","water-security","Water Security")
    indicator=create_entity(client,write_headers,"indicator","water-stress","Water Stress")
    dataset=create_entity(client,write_headers,"dataset","water-data","Water Dataset")
    tool=create_entity(client,write_headers,"tool","water-tool","Water Tool")
    first=create_relationship(client,write_headers,article,"about",concept)
    create_relationship(client,write_headers,concept,"measured_by",indicator)
    create_relationship(client,write_headers,indicator,"measured_by",dataset)
    create_relationship(client,write_headers,tool,"applies_to",concept)

    path=client.get("/v1/graph/path",params={"source_id":article,"target_id":dataset,"depth":4,"direction":"outbound"})
    assert path.status_code==200
    assert path.json()["paths"][0]["length"]==3

    neighborhood=client.get(f"/v1/graph/{concept}/neighborhood")
    assert neighborhood.status_code==200
    assert neighborhood.json()["total_relationships"]>=3

    rec=client.get(f"/v1/graph/{concept}/recommendations",params={"target_type":"tool"})
    assert rec.status_code==200
    assert rec.json()["items"][0]["entity"]["id"]==tool

    jsonld=client.get(f"/v1/entities/{concept}/jsonld")
    assert jsonld.status_code==200
    assert jsonld.json()["@id"]==concept
    assert jsonld.json()["sc:relationships"]

    review=client.post(f"/v1/relationships/{first['id']}/reviews",headers=write_headers,json={"decision":"reject","reviewer":"test-reviewer","note":"Testing review history.","metadata":{"reason":"test"}})
    assert review.status_code==201
    assert review.json()["resulting_status"]=="rejected"

    reviews=client.get("/v1/relationship-reviews",params={"relationship_id":first["id"]})
    assert reviews.status_code==200
    assert len(reviews.json())==1

def test_public_explorer_page(client):
    response=client.get("/explorer")
    assert response.status_code==200
    assert "Knowledge Explorer" in response.text
    assert "/v1/entities" in response.text
