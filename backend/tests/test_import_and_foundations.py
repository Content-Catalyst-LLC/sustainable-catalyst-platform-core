def test_manifest_import_is_idempotent(client, write_headers):
    manifest = {
        "source_name": "test-site-intelligence",
        "entities": [
            {
                "entity_type": "source",
                "slug": "world-bank",
                "name": "World Bank",
                "metadata": {},
                "aliases": [],
            }
        ],
        "relationships": [],
    }

    first = client.post(
        "/v1/imports/site-intelligence",
        headers=write_headers,
        json=manifest,
    )
    assert first.status_code == 200
    assert first.json()["entities_created"] == 1

    second = client.post(
        "/v1/imports/site-intelligence",
        headers=write_headers,
        json=manifest,
    )
    assert second.status_code == 200
    assert second.json()["entities_updated"] == 1


def test_evidence_and_validation_foundations(client, write_headers):
    source = client.post(
        "/v1/entities",
        headers=write_headers,
        json={
            "entity_type": "source",
            "slug": "un-data",
            "name": "UN Data",
            "metadata": {},
            "aliases": [],
        },
    ).json()["id"]

    evidence = client.post(
        "/v1/evidence-foundations",
        headers=write_headers,
        json={
            "evidence_type": "source-record",
            "source_entity_id": source,
            "methodology": "Initial registry foundation.",
            "confidence": 0.8,
            "review_status": "unreviewed",
            "provenance": {"retrieved_by": "test"},
        },
    )
    assert evidence.status_code == 201
    assert evidence.json()["source_entity_id"] == source

    validation = client.post(
        "/v1/validation-events",
        headers=write_headers,
        json={
            "entity_id": source,
            "component": "source-registry",
            "check_name": "schema-validation",
            "status": "passed",
            "severity": "info",
            "details": {"schema": "source-v1"},
        },
    )
    assert validation.status_code == 201

    stats = client.get("/v1/stats")
    assert stats.status_code == 200
    body = stats.json()
    assert body["evidence_foundations"] == 1
    assert body["validation_events"] == 1
