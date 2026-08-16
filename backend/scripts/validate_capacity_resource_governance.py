from __future__ import annotations

from datetime import timedelta
from app.config import Settings
from app.database import Database
from app.migrations import migration_status, run_migrations
from app.services import capacity


def main():
    settings = Settings.from_env()
    database = Database(settings.database_url)
    run_migrations(database)
    status = migration_status(database)
    assert settings.version == "2.26.0"
    assert "0027" in status["applied"] and not status["pending"]
    with database.session_factory() as db:
        profile = capacity.upsert_profile(
            db, settings,
            resource_type="validator",
            resource_key="bounded-demand",
            product_scope="platform-core",
            unit="units",
            capacity_limit=100.0,
            metadata={"validator": True},
        )
        at = capacity.now() - timedelta(hours=2)
        for i, value in enumerate((20.0, 30.0, 40.0)):
            capacity.record_observation(db, settings, profile.id, used_value=value, source="validator", observed_at=at + timedelta(hours=i))
        forecast = capacity.generate_forecast(db, settings, profile.id, horizon_hours=2)
        decision = capacity.assess_profile(db, settings, profile.id, generate=False)
        snapshot = capacity.readiness(db, settings)
        assert forecast.observed_points >= settings.capacity_min_forecast_points
        assert forecast.method == "bounded-linear"
        assert forecast.evidence_json["automatic_scaling"] is False
        assert decision.automatic_actuation is False
        assert snapshot["automatic_infrastructure_purchase"] is False
        assert snapshot["hard_admission_control"] is False
        print({
            "version": settings.version,
            "migration_0027_applied": True,
            "forecast_state": forecast.state,
            "confidence": forecast.confidence,
            "decision": decision.action,
            "automatic_actuation": False,
        })
    print("PASS - Core 2.26.0 capacity forecasting and resource governance validation")


if __name__ == "__main__":
    main()
