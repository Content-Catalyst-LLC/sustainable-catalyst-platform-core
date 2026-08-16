from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.config import Settings
from app.main import create_app
from fastapi.testclient import TestClient


def create_profile(client, headers, **overrides):
    payload = {
        "resource_type": "storage",
        "resource_key": "research-archive-bytes",
        "product_scope": "library",
        "unit": "bytes",
        "capacity_limit": 1000,
        "forecast_horizon_hours": 4,
    }
    payload.update(overrides)
    response = client.post("/v1/capacity/profiles", headers=headers, json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def test_v2240_release_and_migration_0027(client):
    assert client.get("/health").json()["version"] == "2.26.0"
    body = client.get("/v1/capacity/readiness").json()
    assert body["release"] == "2.26.0"
    assert body["migration_0027_applied"] is True
    assert body["pending_migrations"] == []
    assert body["automatic_scaling"] is False
    assert body["automatic_infrastructure_purchase"] is False
    assert body["hard_admission_control"] is False


def test_profile_upsert_and_threshold_validation(client, write_headers):
    first = create_profile(client, write_headers)
    second = create_profile(client, write_headers, capacity_limit=2000)
    assert second["id"] == first["id"]
    assert second["capacity_limit"] == 2000
    bad = client.post("/v1/capacity/profiles", headers=write_headers, json={
        "resource_type": "queue", "resource_key": "x", "capacity_limit": 10,
        "warning_utilization": 0.95, "critical_utilization": 0.90,
    })
    assert bad.status_code == 422


def test_bounded_forecast_tracks_growth_and_capacity_risk(client, write_headers):
    profile = create_profile(client, write_headers, capacity_limit=100)
    base = datetime.now(timezone.utc) - timedelta(hours=3)
    for index, value in enumerate((40, 55, 70, 85)):
        r = client.post(f"/v1/capacity/profiles/{profile['id']}/observations", headers=write_headers, json={
            "used_value": value,
            "source": "test",
            "observed_at": (base + timedelta(hours=index)).isoformat(),
        })
        assert r.status_code == 200, r.text
    forecast = client.post(f"/v1/capacity/profiles/{profile['id']}/forecast?horizon_hours=2", headers=write_headers).json()
    assert forecast["observed_points"] == 4
    assert forecast["slope_per_hour"] > 0
    assert forecast["predicted_value"] >= 100
    assert forecast["state"] == "critical"
    assert forecast["hours_to_capacity"] is not None
    assert forecast["evidence"]["forecast_is_advisory"] is True
    assert forecast["evidence"]["automatic_scaling"] is False


def test_insufficient_forecast_is_explicit(client, write_headers):
    profile = create_profile(client, write_headers, resource_key="few-points")
    client.post(f"/v1/capacity/profiles/{profile['id']}/observations", headers=write_headers, json={"used_value": 10})
    forecast = client.post(f"/v1/capacity/profiles/{profile['id']}/forecast", headers=write_headers).json()
    assert forecast["state"] == "insufficient-data"
    assert forecast["confidence"] == 0.0
    assert forecast["predicted_value"] is None


def test_budget_soft_limit_is_advisory_not_actuation(client, write_headers):
    profile = create_profile(client, write_headers, resource_type="requests", resource_key="library-rpm", unit="requests/minute", capacity_limit=1000)
    budget = client.post("/v1/capacity/budgets", headers=write_headers, json={
        "budget_key": "library-request-budget",
        "name": "Library request budget",
        "product_scope": "library",
        "resource_type": "requests",
        "resource_key": "library-rpm",
        "unit": "requests/minute",
        "budget_limit": 500,
        "warning_fraction": 0.8,
        "enforcement_mode": "soft-limit",
    })
    assert budget.status_code == 200, budget.text
    base = datetime.now(timezone.utc) - timedelta(hours=2)
    for index, value in enumerate((450, 510, 550)):
        client.post(f"/v1/capacity/profiles/{profile['id']}/observations", headers=write_headers, json={"used_value": value, "observed_at": (base + timedelta(hours=index)).isoformat()})
    decision = client.post(f"/v1/capacity/profiles/{profile['id']}/assess", headers=write_headers).json()
    assert decision["action"] == "advisory-soft-block"
    assert decision["reason"] == "budget-limit-reached"
    assert decision["automatic_actuation"] is False
    assert decision["evidence"]["automatic_rejection"] is False


def test_runtime_observation_materializes_existing_scale_pressure(client, write_headers):
    job = client.post("/v1/scale/jobs", headers=write_headers, json={
        "job_type": "capacity-test", "idempotency_key": "capacity-test", "partitions": [{"key": "a"}, {"key": "b"}]
    })
    assert job.status_code == 200
    response = client.post("/v1/capacity/runtime/observe", headers=write_headers)
    assert response.status_code == 200, response.text
    assert len(response.json()["observations"]) == 3
    profiles = client.get("/v1/capacity/profiles?enabled_only=true").json()["items"]
    keys = {item["resource_key"] for item in profiles}
    assert {"active-jobs", "queued-partitions", "pending-work-items"}.issubset(keys)


def test_capacity_ready_requires_forecast_coverage(client, write_headers):
    profile = create_profile(client, write_headers, resource_key="covered", capacity_limit=1000)
    base = datetime.now(timezone.utc) - timedelta(hours=2)
    for index, value in enumerate((100, 110, 120)):
        client.post(f"/v1/capacity/profiles/{profile['id']}/observations", headers=write_headers, json={"used_value": value, "observed_at": (base + timedelta(hours=index)).isoformat()})
    before = client.get("/v1/capacity/readiness").json()
    assert before["capacity_ready"] is False
    client.post(f"/v1/capacity/profiles/{profile['id']}/forecast", headers=write_headers)
    after = client.get("/v1/capacity/readiness").json()
    assert after["capacity_ready"] is True
    assert after["forecast_covered_profiles"] == 1


def test_capacity_certification_gate_is_optional_and_can_block(tmp_path):
    db_path = tmp_path / "cert.db"
    app = create_app(Settings(database_url=f"sqlite:///{db_path}", certification_require_capacity_ready=True))
    client = TestClient(app)
    response = client.post("/v1/certification/runs")
    assert response.status_code == 200, response.text
    body = response.json()["detail"]
    assert body["state"] == "blocked"
    assert "capacity_resource_governance" in body["blockers"]
    assert body["checks"]["capacity_ready"] is False


def test_public_capacity_status_is_aggregate_only(client):
    response = client.get("/api/v1/capacity/status")
    assert response.status_code in (200, 401, 403)
    if response.status_code == 200:
        data = response.json()["data"]
        assert data["private_capacity_values_exposed"] is False
        assert "capacity_limit" not in data
        assert "predicted_value" not in data


def test_meta_promotes_v2240_capabilities(client):
    body = client.get("/v1/meta").json()
    expected = {
        "capacity_forecasting_resource_governance",
        "capacity_resource_profiles",
        "bounded_linear_capacity_forecasts",
        "resource_budgets",
        "advisory_soft_limit_governance",
        "capacity_certification_gate",
    }
    assert expected.issubset(set(body["capabilities"]))
    assert expected.isdisjoint(set(body["deferred_capabilities"]))


def test_observation_retention_prunes_old_points(client, write_headers):
    profile = create_profile(client, write_headers, resource_key="retention")
    client.app.state.settings.__dict__["capacity_observation_retention_hours"] = 24
    old = datetime.now(timezone.utc) - timedelta(days=2)
    response = client.post(f"/v1/capacity/profiles/{profile['id']}/observations", headers=write_headers, json={"used_value": 1, "observed_at": old.isoformat()})
    assert response.status_code == 200
    rows = client.get(f"/v1/capacity/profiles/{profile['id']}/observations").json()["items"]
    assert rows == []
