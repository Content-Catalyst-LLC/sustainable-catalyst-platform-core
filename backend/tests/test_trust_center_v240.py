from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.hashing import sha256_text
from app.models import ApiCredential, EvaluationRun, TrustFinding, WebhookEvent


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
    assert response.status_code == 201, response.text
    return response.json()["id"]


def create_application_and_key(client, write_headers, scopes):
    application = client.post(
        "/v1/developer/applications",
        headers=write_headers,
        json={
            "name": "Trust Center Integration",
            "owner_name": "Trust Developer",
            "owner_email": "trust@example.com",
            "organization": "Example",
            "website_url": "https://example.com",
            "use_case": "Read machine-readable Sustainable Catalyst Trust Center evaluation and incident records.",
            "status": "approved",
            "plan_id": "free",
            "metadata": {},
            "actor": "platform-administrator",
        },
    )
    assert application.status_code == 201, application.text
    issued = client.post(
        f"/v1/developer/applications/{application.json()['id']}/credentials",
        headers=write_headers,
        json={
            "label": "Trust reader",
            "scopes": scopes,
            "created_by": "platform-administrator",
            "metadata": {},
        },
    )
    assert issued.status_code == 201, issued.text
    return issued.json()["api_key"]


def public_headers(key):
    return {"Authorization": f"Bearer {key}"}


def test_evaluation_catalog_and_public_trust_center(client):
    definitions = client.get("/v1/trust/definitions")
    assert definitions.status_code == 200
    ids = {item["id"] for item in definitions.json()}
    assert {
        "ledger-integrity",
        "public-api-readiness",
        "evidence-review-coverage",
        "connector-freshness",
        "calculator-validation",
        "ai-grounding",
        "accessibility-conformance",
        "webhook-delivery-reliability",
    }.issubset(ids)

    page = client.get("/trust")
    status_json = client.get("/trust/status.json")
    evaluations_json = client.get("/trust/evaluations.json")
    assert page.status_code == 200
    assert "Trust Center" in page.text
    assert status_json.status_code == 200
    assert status_json.json()["overall_status"] == "unknown"
    assert status_json.json()["ledger_valid"] is True
    assert evaluations_json.status_code == 200
    assert len(evaluations_json.json()) >= 8


def test_platform_evaluation_suite_and_immutable_runs(client, write_headers):
    response = client.post(
        "/v1/trust/run-suite",
        headers=write_headers,
        json={
            "definition_ids": ["ledger-integrity", "public-api-readiness"],
            "triggered_by": "release-validation",
            "contexts": {},
            "environment": {"release": "2.4.0"},
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total"] == 2
    assert body["passed"] == 2
    assert all(run["content_hash"] and len(run["content_hash"]) == 64 for run in body["runs"])
    assert all(run["checks"] for run in body["runs"])

    trust_status = client.get("/v1/trust/status")
    assert trust_status.status_code == 200
    assert trust_status.json()["overall_status"] == "operational"

    database = client.app.state.database
    with database.session_factory() as db:
        run = db.scalar(select(EvaluationRun).order_by(EvaluationRun.created_at).limit(1))
        run.summary = "tampered"
        with pytest.raises(RuntimeError, match="immutable"):
            db.commit()
        db.rollback()


def test_connector_freshness_failure_creates_audited_finding(client, write_headers):
    connector_id = create_entity(client, write_headers, "connector", "climate-connector", "Climate Connector")
    old_time = datetime.now(timezone.utc) - timedelta(hours=100)
    response = client.post(
        "/v1/trust/definitions/connector-freshness/runs",
        headers=write_headers,
        json={
            "target_entity_id": connector_id,
            "triggered_by": "site-intelligence",
            "observations": {
                "last_success_at": old_time.isoformat(),
                "max_age_hours": 24,
                "connector_status": "active",
            },
            "environment": {"connector": "test"},
            "evidence_references": [],
        },
    )
    assert response.status_code == 201, response.text
    run = response.json()
    assert run["status"] == "failed"
    assert run["checks"][0]["status"] == "failed"

    findings = client.get("/v1/trust/findings?status=open")
    assert findings.status_code == 200
    assert len(findings.json()) == 1
    assert findings.json()[0]["evaluation_run_id"] == run["id"]

    database = client.app.state.database
    with database.session_factory() as db:
        event = db.scalar(
            select(WebhookEvent)
            .where(WebhookEvent.event_type == "trust.finding.created")
            .order_by(WebhookEvent.created_at.desc())
        )
        assert event is not None
        assert event.resource_id == findings.json()[0]["id"]

    public_status = client.get("/trust/status.json").json()
    assert public_status["overall_status"] == "degraded"
    assert public_status["open_findings"] == 1


def test_calculator_ai_and_accessibility_evaluators(client, write_headers):
    calculator = client.post(
        "/v1/trust/definitions/calculator-validation/runs",
        headers=write_headers,
        json={
            "triggered_by": "workbench-ci",
            "observations": {
                "total_cases": 100,
                "passed_cases": 100,
                "tolerance_failures": 0,
                "edge_cases_total": 20,
                "edge_cases_passed": 20,
            },
            "environment": {"python": "3.12"},
            "evidence_references": ["sc:trace:test"],
        },
    )
    assert calculator.status_code == 201
    assert calculator.json()["status"] == "passed"
    assert calculator.json()["grade"] == "A"

    ai = client.post(
        "/v1/trust/definitions/ai-grounding/runs",
        headers=write_headers,
        json={
            "triggered_by": "research-librarian-evaluation",
            "observations": {
                "citation_coverage": 0.98,
                "unsupported_claim_rate": 0.01,
                "source_relevance": 0.96,
                "scope_gate_pass_rate": 0.99,
            },
            "environment": {"provider": "gemini"},
            "evidence_references": [],
        },
    )
    assert ai.status_code == 201
    assert ai.json()["status"] == "passed"
    assert len(ai.json()["checks"]) == 4

    accessibility = client.post(
        "/v1/trust/definitions/accessibility-conformance/runs",
        headers=write_headers,
        json={
            "triggered_by": "accessibility-review",
            "observations": {
                "target": "WCAG 2.2 AA",
                "total_checks": 100,
                "passed_checks": 98,
                "critical_failures": 0,
                "manual_checks_pending": 2,
            },
            "environment": {},
            "evidence_references": [],
        },
    )
    assert accessibility.status_code == 201
    assert accessibility.json()["status"] == "warning"
    assert accessibility.json()["score"] == 98.0


def test_incident_lifecycle_changes_aggregate_status(client, write_headers):
    incident = client.post(
        "/v1/trust/incidents",
        headers=write_headers,
        json={
            "title": "Delayed source connector updates",
            "severity": "high",
            "status": "investigating",
            "summary": "One public source connector is not refreshing on schedule.",
            "impact": "Some public freshness indicators may be delayed.",
            "affected_entity_ids": [],
            "public": True,
            "metadata": {},
            "actor": "platform-operations",
        },
    )
    assert incident.status_code == 201, incident.text
    incident_id = incident.json()["id"]
    status = client.get("/trust/status.json").json()
    assert status["overall_status"] == "degraded"
    assert status["active_incidents"][0]["id"] == incident_id

    resolved = client.patch(
        f"/v1/trust/incidents/{incident_id}",
        headers=write_headers,
        json={
            "status": "resolved",
            "root_cause": "Upstream API maintenance.",
            "remediation": "Connector retried successfully.",
            "actor": "platform-operations",
        },
    )
    assert resolved.status_code == 200
    assert resolved.json()["resolved_at"]
    assert client.get("/trust/status.json").json()["active_incidents"] == []


def test_limitations_and_attestations_are_disclosed_and_revocable(client, write_headers):
    tool_id = create_entity(client, write_headers, "tool", "trust-test-tool", "Trust Test Tool")
    limitation = client.post(
        "/v1/trust/limitations",
        headers=write_headers,
        json={
            "domain": "calculation-quality",
            "title": "Experimental calculator coverage",
            "description": "Some experimental calculators do not yet have complete edge-case validation.",
            "impact": "Results require additional review.",
            "mitigation": "Experimental status is displayed and exports include validation state.",
            "affected_entity_ids": [tool_id],
            "status": "active",
            "public": True,
            "metadata": {},
            "actor": "workbench-maintainer",
        },
    )
    assert limitation.status_code == 201

    attestation = client.post(
        "/v1/trust/attestations",
        headers=write_headers,
        json={
            "subject_entity_id": tool_id,
            "statement": "The published validation suite completed without failures for this release.",
            "scope": "release-validation",
            "issuer": "Sustainable Catalyst Platform Core",
            "evidence_references": ["sc:evaluation-run:example"],
            "public": True,
            "metadata": {"release": "2.4.0"},
            "actor": "release-manager",
        },
    )
    assert attestation.status_code == 201, attestation.text
    assert len(attestation.json()["content_hash"]) == 64

    public_status = client.get("/trust/status.json").json()
    assert public_status["known_limitations"][0]["id"] == limitation.json()["id"]
    assert public_status["active_attestations"][0]["id"] == attestation.json()["id"]

    revoked = client.post(
        f"/v1/trust/attestations/{attestation.json()['id']}/revoke",
        headers=write_headers,
        json={"reason": "Superseded by a later release evaluation.", "revoked_by": "release-manager"},
    )
    assert revoked.status_code == 200
    assert revoked.json()["status"] == "revoked"
    assert client.get("/trust/status.json").json()["active_attestations"] == []


def test_unified_public_api_trust_scope_and_openapi(client, write_headers):
    key = create_application_and_key(client, write_headers, ["trust:read"])
    status = client.get("/api/v1/trust/status", headers=public_headers(key))
    evaluations = client.get("/api/v1/trust/evaluations", headers=public_headers(key))
    forbidden = client.get("/api/v1/entities", headers=public_headers(key))
    assert status.status_code == 200
    assert status.json()["meta"]["documentation"] == "/trust"
    assert evaluations.status_code == 200
    assert forbidden.status_code == 403

    openapi = client.get("/developers/openapi.json").json()
    assert "/api/v1/trust/status" in openapi["paths"]


def test_private_trust_records_are_not_public(client, write_headers):
    private_limitation = client.post(
        "/v1/trust/limitations",
        headers=write_headers,
        json={
            "domain": "security",
            "title": "Internal limitation",
            "description": "Internal-only disclosure.",
            "status": "active",
            "affected_entity_ids": [],
            "public": False,
            "metadata": {},
            "actor": "security-reviewer",
        },
    )
    private_incident = client.post(
        "/v1/trust/incidents",
        headers=write_headers,
        json={
            "title": "Internal incident",
            "severity": "critical",
            "status": "investigating",
            "summary": "Internal-only incident record.",
            "affected_entity_ids": [],
            "public": False,
            "metadata": {},
            "actor": "security-reviewer",
        },
    )
    assert private_limitation.status_code == 201
    assert private_incident.status_code == 201

    public_status = client.get("/trust/status.json").json()
    assert public_status["active_incidents"] == []
    assert public_status["known_limitations"] == []
    admin_status = client.get("/v1/trust/status").json()
    assert admin_status["overall_status"] == "critical"


def test_custom_recorded_evaluation_and_trust_statistics(client, write_headers):
    definition = client.post(
        "/v1/trust/definitions",
        headers=write_headers,
        json={
            "id": "editorial-source-review",
            "name": "Editorial Source Review",
            "domain": "editorial-quality",
            "description": "Recorded editorial review criteria.",
            "methodology": "A reviewer records explicit check-level results.",
            "evaluator_kind": "recorded",
            "target_type": "article",
            "thresholds": {"pass_score": 90, "warning_score": 75},
            "cadence": "publication",
            "severity_on_failure": "high",
            "public": True,
            "active": True,
            "version": "1.0",
            "sort_order": 90,
            "metadata": {},
            "actor": "editorial-governance",
        },
    )
    assert definition.status_code == 201
    run = client.post(
        "/v1/trust/definitions/editorial-source-review/runs",
        headers=write_headers,
        json={
            "triggered_by": "editorial-reviewer",
            "observations": {
                "checks": [
                    {
                        "check_key": "primary-authorities",
                        "name": "Primary authority coverage",
                        "status": "passed",
                        "score": 100,
                        "observed": {"count": 5},
                        "expected": {"minimum": 3},
                    },
                    {
                        "check_key": "citation-completeness",
                        "name": "Citation completeness",
                        "status": "failed",
                        "score": 50,
                        "severity": "high",
                        "details": {"reason": "Two material assertions lack citations."},
                    },
                ]
            },
            "environment": {},
            "evidence_references": [],
        },
    )
    assert run.status_code == 201
    assert run.json()["status"] == "failed"
    assert run.json()["score"] == 75.0

    stats = client.get("/v1/stats")
    assert stats.status_code == 200
    body = stats.json()
    assert body["evaluation_definitions"] >= 9
    assert body["evaluation_runs"] == 1
    assert body["evaluation_check_results"] == 2
    assert body["trust_findings"] == 1
