from __future__ import annotations

from sqlalchemy import select, text
import pytest

from app.models import WorkflowTransition


def create_entity(client, headers, slug="signature-subject"):
    response = client.post(
        "/v1/entities",
        headers=headers,
        json={
            "entity_type": "concept",
            "slug": slug,
            "name": slug.replace("-", " ").title(),
            "description": "A subject used by the signature dossier tests.",
            "visibility": "public",
            "metadata": {},
            "aliases": [],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def create_run(client, headers, subject_id, *, public=True):
    response = client.post(
        "/v1/workflow-runs",
        headers=headers,
        json={
            "definition_id": "evidence-assurance-dossier",
            "title": "Evidence Assurance Test Workflow",
            "subject_entity_id": subject_id,
            "requested_by": "decision-studio",
            "owner": "platform-reviewer",
            "context": {"decision": "test"},
            "public": public,
            "metadata": {},
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def complete_run(client, headers, run):
    run_id = run["id"]
    started = client.post(
        f"/v1/workflow-runs/{run_id}/start",
        headers=headers,
        json={"actor": "workflow-orchestrator", "reason": "Begin the end-to-end route."},
    )
    assert started.status_code == 200, started.text
    current = started.json()
    for step in current["steps"]:
        first = client.post(
            f"/v1/workflow-runs/{run_id}/steps/{step['step_key']}/transition",
            headers=headers,
            json={
                "status": "in_progress",
                "actor": step["product"],
                "reason": "Stage started.",
                "input_references": [f"sc:input:{step['step_key']}"],
                "payload": {},
            },
        )
        assert first.status_code == 200, first.text
        second = client.post(
            f"/v1/workflow-runs/{run_id}/steps/{step['step_key']}/transition",
            headers=headers,
            json={
                "status": "completed",
                "actor": step["product"],
                "reason": "Stage completed.",
                "output_references": [f"sc:output:{step['step_key']}"],
                "notes": "Validated test output.",
                "payload": {"validation": "passed"},
            },
        )
        assert second.status_code == 200, second.text
        current = second.json()
    assert current["status"] == "completed"
    assert len(current["content_hash"]) == 64
    return current


def create_dossier(client, headers, run_id, subject_id, *, visibility="public"):
    response = client.post(
        "/v1/dossiers",
        headers=headers,
        json={
            "workflow_run_id": run_id,
            "subject_entity_id": subject_id,
            "title": "Signed Evidence Assurance Dossier",
            "purpose": "Freeze and verify the evidence, workflow, and trust context for the test decision.",
            "version": "1.0",
            "visibility": visibility,
            "metadata": {"release": "2.5.0"},
            "actor": "decision-studio",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def add_record(client, headers, dossier_id, record_type, record_id, *, section="Evidence", public=True):
    response = client.post(
        f"/v1/dossiers/{dossier_id}/records",
        headers=headers,
        json={
            "section": section,
            "record_type": record_type,
            "record_id": record_id,
            "label": f"{record_type}: {record_id}",
            "sort_order": 100,
            "public": public,
            "metadata": {},
            "actor": "dossier-assembler",
        },
    )
    assert response.status_code == 201, response.text
    assert len(response.json()["snapshot_hash"]) == 64
    return response.json()


def approve(client, headers, dossier_id, *, signer="reviewer@example.org", decision="approve"):
    response = client.post(
        f"/v1/dossiers/{dossier_id}/approvals",
        headers=headers,
        json={
            "decision": decision,
            "signer": signer,
            "role": "Evidence Reviewer",
            "statement": "I reviewed the frozen records and approve this dossier." if decision == "approve" else "Changes are required.",
            "evidence_references": [],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def finalize(client, headers, dossier_id):
    return client.post(
        f"/v1/dossiers/{dossier_id}/finalize",
        headers=headers,
        json={"signed_by": "Sustainable Catalyst Platform Core", "actor": "platform-signing-service"},
    )


def issue_public_key(client, headers, scopes):
    application = client.post(
        "/v1/developer/applications",
        headers=headers,
        json={
            "name": "Dossier API Test",
            "owner_name": "Test Developer",
            "owner_email": "dossier@example.org",
            "organization": "Example",
            "website_url": "https://example.org",
            "use_case": "Read public Sustainable Catalyst workflow and signature dossier records for an external assurance integration.",
            "status": "approved",
            "plan_id": "free",
            "metadata": {},
            "actor": "platform-administrator",
        },
    )
    assert application.status_code == 201, application.text
    issued = client.post(
        f"/v1/developer/applications/{application.json()['id']}/credentials",
        headers=headers,
        json={"label": "Dossier key", "scopes": scopes, "created_by": "platform-administrator", "metadata": {}},
    )
    assert issued.status_code == 201, issued.text
    return issued.json()["api_key"]


def test_workflow_definitions_seed_and_dependency_enforcement(client, write_headers):
    definitions = client.get("/v1/workflow-definitions")
    assert definitions.status_code == 200
    ids = {item["id"] for item in definitions.json()}
    assert {"research-to-signature-dossier", "evidence-assurance-dossier", "dashboard-publication-dossier"}.issubset(ids)

    subject_id = create_entity(client, write_headers, "dependency-subject")
    run = create_run(client, write_headers, subject_id)
    run_id = run["id"]
    started = client.post(f"/v1/workflow-runs/{run_id}/start", headers=write_headers, json={"actor": "orchestrator"})
    assert started.status_code == 200

    blocked = client.post(
        f"/v1/workflow-runs/{run_id}/steps/collect/transition",
        headers=write_headers,
        json={"status": "in_progress", "actor": "research-librarian", "payload": {}},
    )
    assert blocked.status_code == 409
    assert "scope" in blocked.json()["detail"]["blocking_steps"]


def test_end_to_end_workflow_and_transition_immutability(client, write_headers):
    subject_id = create_entity(client, write_headers, "complete-workflow-subject")
    completed = complete_run(client, write_headers, create_run(client, write_headers, subject_id))
    assert completed["current_step_key"] is None
    assert all(step["status"] == "completed" for step in completed["steps"])
    assert len(completed["transitions"]) >= len(completed["steps"]) * 2 + 2

    database = client.app.state.database
    with database.session_factory() as db:
        transition = db.scalar(select(WorkflowTransition).where(WorkflowTransition.run_id == completed["id"]).limit(1))
        transition.reason = "Attempted mutation"
        with pytest.raises(RuntimeError, match="append-only"):
            db.commit()
        db.rollback()


def test_signature_dossier_finalization_and_frozen_live_record(client, write_headers):
    subject_id = create_entity(client, write_headers, "frozen-record-subject")
    workflow = complete_run(client, write_headers, create_run(client, write_headers, subject_id))
    dossier = create_dossier(client, write_headers, workflow["id"], subject_id)
    add_record(client, write_headers, dossier["id"], "entity", subject_id, section="Subject")
    add_record(client, write_headers, dossier["id"], "workflow_run", workflow["id"], section="Workflow")
    add_record(client, write_headers, dossier["id"], "trust_status", "platform", section="Trust")
    approve(client, write_headers, dossier["id"])

    final = finalize(client, write_headers, dossier["id"])
    assert final.status_code == 200, final.text
    body = final.json()
    assert body["status"] == "finalized"
    assert body["signature_algorithm"] == "HMAC-SHA256"
    assert len(body["dossier_hash"]) == 64
    assert len(body["platform_signature"]) == 64

    verified = client.get(f"/v1/dossiers/{dossier['id']}/verify")
    assert verified.status_code == 200
    assert verified.json()["valid"] is True

    entity_update = client.patch(
        f"/v1/entities/{subject_id}",
        headers=write_headers,
        json={"name": "Changed After Dossier Finalization"},
    )
    assert entity_update.status_code == 200
    still_verified = client.get(f"/v1/dossiers/{dossier['id']}/verify")
    assert still_verified.json()["valid"] is True


def test_dossier_tampering_is_detected(client, write_headers):
    subject_id = create_entity(client, write_headers, "tamper-dossier-subject")
    workflow = complete_run(client, write_headers, create_run(client, write_headers, subject_id))
    dossier = create_dossier(client, write_headers, workflow["id"], subject_id)
    add_record(client, write_headers, dossier["id"], "entity", subject_id)
    approve(client, write_headers, dossier["id"])
    assert finalize(client, write_headers, dossier["id"]).status_code == 200

    database = client.app.state.database
    with database.session_factory() as db:
        db.execute(text("UPDATE signature_dossiers SET snapshot_json = :payload WHERE id = :id"), {"payload": '{"tampered":true}', "id": dossier["id"]})
        db.commit()

    verification = client.get(f"/v1/dossiers/{dossier['id']}/verify")
    assert verification.status_code == 200
    assert verification.json()["valid"] is False
    assert verification.json()["hash_matches"] is False


def test_latest_approval_state_controls_finalization(client, write_headers):
    subject_id = create_entity(client, write_headers, "approval-state-subject")
    workflow = complete_run(client, write_headers, create_run(client, write_headers, subject_id))
    dossier = create_dossier(client, write_headers, workflow["id"], subject_id)
    add_record(client, write_headers, dossier["id"], "entity", subject_id)
    approve(client, write_headers, dossier["id"], signer="reviewer@example.org", decision="request_changes")

    blocked = finalize(client, write_headers, dossier["id"])
    assert blocked.status_code == 409

    approve(client, write_headers, dossier["id"], signer="reviewer@example.org", decision="approve")
    finalized = finalize(client, write_headers, dossier["id"])
    assert finalized.status_code == 200


def test_public_api_scopes_and_private_record_filtering(client, write_headers):
    subject_id = create_entity(client, write_headers, "public-dossier-subject")
    workflow = complete_run(client, write_headers, create_run(client, write_headers, subject_id, public=True))
    dossier = create_dossier(client, write_headers, workflow["id"], subject_id, visibility="public")
    add_record(client, write_headers, dossier["id"], "entity", subject_id, public=True)
    add_record(client, write_headers, dossier["id"], "workflow_run", workflow["id"], section="Internal", public=False)
    approve(client, write_headers, dossier["id"])
    assert finalize(client, write_headers, dossier["id"]).status_code == 200

    insufficient_key = issue_public_key(client, write_headers, ["public:status"])
    denied = client.get("/api/v1/dossiers", headers={"Authorization": f"Bearer {insufficient_key}"})
    assert denied.status_code == 403

    api_key = issue_public_key(client, write_headers, ["dossier:read", "workflow:read"])
    listing = client.get("/api/v1/dossiers", headers={"Authorization": f"Bearer {api_key}"})
    assert listing.status_code == 200, listing.text
    assert listing.json()["data"][0]["id"] == dossier["id"]
    detail = client.get(f"/api/v1/dossiers/{dossier['id']}", headers={"Authorization": f"Bearer {api_key}"})
    assert detail.status_code == 200
    assert len(detail.json()["data"]["records"]) == 1
    assert all(record["public"] for record in detail.json()["data"]["canonical_snapshot"]["records"])
    verification = client.get(f"/api/v1/dossiers/{dossier['id']}/verify", headers={"Authorization": f"Bearer {api_key}"})
    assert verification.status_code == 200
    assert verification.json()["data"]["valid"] is True


def test_dossier_center_and_stats(client, write_headers):
    page = client.get("/dossier-center")
    assert page.status_code == 200
    assert "Signature Dossiers" in page.text
    assert "/public/dossiers" in page.text

    stats = client.get("/v1/workflow-platform/stats")
    assert stats.status_code == 200
    assert stats.json()["workflow_definitions"] >= 3
