from __future__ import annotations

import os
from pathlib import Path

from app.config import Settings
from app.database import Database
from app.migrations import migration_status, run_migrations
from app.services import credentials


def main() -> None:
    settings = Settings.from_env()
    database = Database(settings.database_url)
    run_migrations(database)
    status = migration_status(database)
    assert settings.version == "2.26.0", settings.version
    assert "0028" in status["applied"] and not status["pending"], status

    with database.session_factory() as db:
        row = credentials.upsert_credential(
            db,
            settings,
            credential_key="validator-webhook-signing",
            name="Validator webhook signing",
            credential_type="webhook-signing-key",
            purpose="Validate secret-free lifecycle governance",
            secret_reference="env:SC_CORE_WEBHOOK_SIGNING_SECRET",
            allowed_consumers=["validator"],
            allowed_operations=["sign"],
            rotation_interval_days=90,
            overlap_minutes=5,
        )
        v1 = credentials.register_key_version(db, settings, row.id, key_id="validator-v1", algorithm="hmac-sha256", fingerprint_sha256="a" * 64)
        first = credentials.rotate(db, row.id, v1.id, requested_by="release-validator")
        assert first.state == "complete"
        v2 = credentials.register_key_version(db, settings, row.id, key_id="validator-v2", algorithm="hmac-sha256", fingerprint_sha256="b" * 64)
        second = credentials.rotate(db, row.id, v2.id, requested_by="release-validator")
        assert second.state == "overlap"
        completed = credentials.complete_rotation(db, second.id, actor="release-validator")
        assert completed.state == "complete"
        use = credentials.record_use(db, row.id, key_version_id=v2.id, service_id="validator", operation="sign", context={"request_id":"v2250","api_key":"strip-me"})
        assert use.context_json == {"request_id":"v2250"}
        ready = credentials.readiness(db, settings)
        assert ready["credential_lifecycle_ready"] is True, ready
        assert ready["secret_values_persisted"] is False
        assert ready["automatic_secret_generation"] is False
        assert ready["automatic_secret_distribution"] is False
        assert ready["automatic_key_rotation"] is False
        public = credentials.public_status(db, settings)
        assert public["secret_values_exposed"] is False
        assert public["secret_references_exposed"] is False
        assert public["key_ids_exposed"] is False
        assert public["fingerprints_exposed"] is False

    print({
        "version": settings.version,
        "migration_0028_applied": True,
        "pending_migrations": [],
        "credential_lifecycle_ready": True,
        "secret_values_persisted": False,
        "automatic_key_rotation": False,
    })
    print("PASS - Core 2.26.0 identity credential and cryptographic key lifecycle validation")


if __name__ == "__main__":
    main()
