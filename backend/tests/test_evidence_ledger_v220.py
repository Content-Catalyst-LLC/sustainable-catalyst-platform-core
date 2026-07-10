from sqlalchemy import select, text
import pytest

from app.models import LedgerEntry


def create_entity(client, headers, entity_type, slug, name):
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


def test_complete_evidence_ledger_workflow(client, write_headers):
    source_id = create_entity(
        client, write_headers, "source", "climate-report", "Climate Report"
    )
    tool_id = create_entity(
        client, write_headers, "tool", "emissions-model", "Emissions Model"
    )
    subject_id = create_entity(
        client, write_headers, "concept", "emissions-reduction", "Emissions Reduction"
    )

    claim_response = client.post(
        "/v1/claims",
        headers=write_headers,
        json={
            "actor": "decision-studio",
            "claim_text": "The intervention reduces annual emissions by 12 percent.",
            "claim_type": "analytical",
            "subject_entity_id": subject_id,
            "status": "draft",
            "visibility": "public",
            "language": "en",
            "metadata": {"scenario": "baseline-comparison"},
        },
    )
    assert claim_response.status_code == 201
    claim_id = claim_response.json()["id"]

    snapshot_response = client.post(
        "/v1/source-snapshots",
        headers=write_headers,
        json={
            "actor": "site-intelligence",
            "source_entity_id": source_id,
            "canonical_url": "https://example.org/climate-report",
            "title": "Climate Report",
            "publisher": "Example Institute",
            "media_type": "text/plain",
            "content": "The modeled intervention reduces annual emissions by 12 percent.",
            "metadata": {"connector": "test"},
        },
    )
    assert snapshot_response.status_code == 201
    snapshot = snapshot_response.json()
    assert len(snapshot["content_hash"]) == 64
    assert "content" not in snapshot
    snapshot_id = snapshot["id"]

    verified = client.post(
        f"/v1/source-snapshots/{snapshot_id}/verify",
        json={"content": "The modeled intervention reduces annual emissions by 12 percent."},
    )
    assert verified.status_code == 200
    assert verified.json()["matches"] is True

    activity_response = client.post(
        "/v1/provenance/activities",
        headers=write_headers,
        json={
            "activity_type": "model-run",
            "name": "Annual emissions scenario",
            "description": "Workbench model execution.",
            "agent": "sustainable-catalyst-workbench",
            "software_entity_id": tool_id,
            "parameters": {"scenario": "intervention"},
            "environment": {"engine": "python"},
            "status": "completed",
            "metadata": {},
        },
    )
    assert activity_response.status_code == 201
    activity_id = activity_response.json()["id"]

    link_response = client.post(
        f"/v1/provenance/activities/{activity_id}/links",
        headers=write_headers,
        json={
            "role": "informed_by",
            "object_type": "claim",
            "object_id": claim_id,
            "metadata": {},
            "actor": "decision-studio",
        },
    )
    assert link_response.status_code == 201

    trace_response = client.post(
        "/v1/calculation-traces",
        headers=write_headers,
        json={
            "tool_entity_id": tool_id,
            "subject_entity_id": subject_id,
            "activity_id": activity_id,
            "run_id": "run-001",
            "inputs": {"baseline_tonnes": 1000, "intervention_tonnes": 880},
            "outputs": {"reduction_percent": 12},
            "formula_version": "1.0",
            "code_version": "workbench-test",
            "runtime": {"python": "3.12"},
            "status": "completed",
            "metadata": {},
            "actor": "sustainable-catalyst-workbench",
        },
    )
    assert trace_response.status_code == 201
    trace_id = trace_response.json()["id"]

    source_evidence_response = client.post(
        "/v1/evidence-records",
        headers=write_headers,
        json={
            "evidence_type": "source-record",
            "stance": "supports",
            "claim_id": claim_id,
            "subject_entity_id": subject_id,
            "source_entity_id": source_id,
            "source_snapshot_id": snapshot_id,
            "statement": "The source reports a 12 percent reduction.",
            "methodology": "Direct comparison with the captured source snapshot.",
            "confidence": 0.88,
            "review_status": "unreviewed",
            "provenance": {"activity_id": activity_id},
            "metadata": {},
            "actor": "decision-studio",
        },
    )
    assert source_evidence_response.status_code == 201
    evidence_id = source_evidence_response.json()["id"]

    trace_evidence_response = client.post(
        "/v1/evidence-records",
        headers=write_headers,
        json={
            "evidence_type": "calculation-trace",
            "stance": "supports",
            "claim_id": claim_id,
            "subject_entity_id": subject_id,
            "calculation_trace_id": trace_id,
            "statement": "The calculation trace reproduces the 12 percent reduction.",
            "confidence": 0.95,
            "review_status": "unreviewed",
            "provenance": {"activity_id": activity_id},
            "metadata": {},
            "actor": "sustainable-catalyst-workbench",
        },
    )
    assert trace_evidence_response.status_code == 201

    assignment_response = client.post(
        f"/v1/evidence-records/{evidence_id}/assignments",
        headers=write_headers,
        json={
            "assignee": "evidence-reviewer",
            "assigned_by": "decision-studio",
            "instructions": "Check the snapshot against the claim.",
            "metadata": {},
        },
    )
    assert assignment_response.status_code == 201
    assignment_id = assignment_response.json()["id"]

    completed = client.post(
        f"/v1/evidence-assignments/{assignment_id}/complete",
        headers=write_headers,
        json={"completed_by": "evidence-reviewer"},
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"

    review_response = client.post(
        f"/v1/evidence-records/{evidence_id}/reviews",
        headers=write_headers,
        json={
            "decision": "approve",
            "reviewer": "evidence-reviewer",
            "note": "Snapshot and claim are consistent.",
            "metadata": {"review_method": "manual"},
        },
    )
    assert review_response.status_code == 201
    assert review_response.json()["resulting_status"] == "verified"

    manifest_response = client.get(f"/v1/evidence/manifests/{claim_id}")
    assert manifest_response.status_code == 200
    manifest = manifest_response.json()
    assert manifest["claim"]["id"] == claim_id
    assert len(manifest["evidence"]) == 2
    assert len(manifest["snapshots"]) == 1
    assert len(manifest["calculation_traces"]) == 1
    assert len(manifest["provenance_activities"]) == 1
    assert len(manifest["reviews"]) == 1
    assert len(manifest["assignments"]) == 1
    assert len(manifest["manifest_hash"]) == 64

    verification = client.get("/v1/ledger/verify")
    assert verification.status_code == 200
    body = verification.json()
    assert body["valid"] is True
    assert body["entries_checked"] >= 10
    assert len(body["head_hash"]) == 64

    stats = client.get("/v1/evidence/stats")
    assert stats.status_code == 200
    assert stats.json()["claims"] == 1
    assert stats.json()["evidence_records"] == 2
    assert stats.json()["ledger_entries"] >= 10


def test_snapshot_verification_detects_different_content(client, write_headers):
    response = client.post(
        "/v1/source-snapshots",
        headers=write_headers,
        json={
            "actor": "test",
            "canonical_url": "https://example.org/source",
            "content": "Original evidence content.",
            "media_type": "text/plain",
            "metadata": {},
        },
    )
    assert response.status_code == 201
    snapshot_id = response.json()["id"]

    verification = client.post(
        f"/v1/source-snapshots/{snapshot_id}/verify",
        json={"content": "Changed evidence content."},
    )
    assert verification.status_code == 200
    assert verification.json()["matches"] is False


def test_ledger_detects_out_of_band_tampering(client, write_headers):
    response = client.post(
        "/v1/claims",
        headers=write_headers,
        json={
            "actor": "test",
            "claim_text": "A claim that will be tampered with in the database.",
            "claim_type": "factual",
            "status": "draft",
            "visibility": "public",
            "language": "en",
            "metadata": {},
        },
    )
    assert response.status_code == 201
    assert client.get("/v1/ledger/verify").json()["valid"] is True

    database = client.app.state.database
    with database.session_factory() as db:
        db.execute(
            text(
                "UPDATE ledger_entries "
                "SET payload_json = :payload "
                "WHERE sequence = 1"
            ),
            {"payload": '{"tampered": true}'},
        )
        db.commit()

    verification = client.get("/v1/ledger/verify")
    assert verification.status_code == 200
    assert verification.json()["valid"] is False
    assert any(
        "payload hash mismatch" in error
        for error in verification.json()["errors"]
    )


def test_ledger_entries_are_append_only_in_orm(client, write_headers):
    response = client.post(
        "/v1/claims",
        headers=write_headers,
        json={
            "actor": "test",
            "claim_text": "Append-only claim.",
            "claim_type": "factual",
            "status": "draft",
            "visibility": "public",
            "language": "en",
            "metadata": {},
        },
    )
    assert response.status_code == 201

    database = client.app.state.database
    with database.session_factory() as db:
        entry = db.scalar(
            select(LedgerEntry).order_by(LedgerEntry.sequence).limit(1)
        )
        entry.action = "changed"
        with pytest.raises(RuntimeError, match="append-only"):
            db.commit()
        db.rollback()


def test_evidence_explorer_page(client):
    response = client.get("/evidence-explorer")
    assert response.status_code == 200
    assert "Evidence Explorer" in response.text
    assert "/v1/ledger/verify" in response.text
    assert "/v1/evidence/manifests/" in response.text
