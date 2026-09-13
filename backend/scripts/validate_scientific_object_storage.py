from __future__ import annotations

import os
import tempfile
from pathlib import Path

from app.config import Settings
from app.database import Database
from app.migrations import migration_status, run_migrations
from app.services import scientific_objects

with tempfile.TemporaryDirectory() as td:
    db_path = Path(td) / "core.db"
    object_root = Path(td) / "scientific-objects"
    settings = Settings(
        database_url=f"sqlite:///{db_path}",
        scientific_object_storage_root=str(object_root),
        observability_request_metrics_enabled=False,
    )
    database = Database(settings.database_url)
    run_migrations(database)

    with database.session_factory() as db:
        ready = scientific_objects.readiness(db, settings)
        assert ready["local_storage_ready"] is True
        assert ready["processing_adapters"] >= 4
        assert ready["executable_adapters"] >= 1
        assert ready["external_fetch_by_core"] is False
        assert ready["credential_values_persisted"] is False

        source = scientific_objects.store_bytes(
            db,
            settings,
            b"time,value\\n2026-09-10,42\\n",
            title="Validator scientific object",
            format_name="csv",
            media_type="text/csv",
            provenance={"validator": "v2.32.0"},
            created_by="release-validator",
        )
        path = scientific_objects.content_path(db, settings, source.id)
        assert path.read_bytes().startswith(b"time,value")
        assert source.integrity_status == "verified"

        external = scientific_objects.register_external_reference(
            db,
            settings,
            uri="https://example.org/data/sample.nc",
            title="Provider-managed validator reference",
            format_name="netcdf",
            content_hash="a" * 64,
            checksum_algorithm="sha256",
            provenance={"validator": "v2.32.0"},
        )
        assert external.backend_key == "external-reference"
        assert external.integrity_status == "declared"

        run = scientific_objects.process_object(
            db,
            settings,
            input_object_id=source.id,
            adapter_key="builtin.object-manifest",
            operation="manifest",
            idempotency_key="validate-v2270-manifest",
            parameters={"purpose": "release-validation"},
            requested_by="release-validator",
        )
        assert run.state == "completed" and run.output_object_id
        derived = scientific_objects.object_or_404(db, run.output_object_id)
        assert derived.parent_object_id == source.id and derived.derived is True
        assert derived.format == "json"

        snapshot = scientific_objects.certification_snapshot(db, settings)
        assert snapshot["scientific_object_storage_ready"] is True
        assert snapshot["arbitrary_code_execution"] is False

    status = migration_status(database)
    assert "0030" in status["applied"] and not status["pending"]
    print({
        "version": "2.32.0",
        "migration_0030_applied": True,
        "storage_backend": "local-filesystem",
        "external_reference_fetch": False,
        "built_in_adapter": "builtin.object-manifest",
        "derived_lineage": True,
        "arbitrary_code_execution": False,
    })
    print("PASS - Core 2.32.0 scientific object storage and processing adapter validation")
