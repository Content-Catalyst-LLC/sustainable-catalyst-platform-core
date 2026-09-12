from __future__ import annotations

import tempfile
from pathlib import Path

from app.config import Settings
from app.database import Database
from app.migrations import migration_status, run_migrations
from app.services import research_objects

with tempfile.TemporaryDirectory() as td:
    db_path = Path(td) / "core.db"
    settings = Settings(database_url=f"sqlite:///{db_path}", observability_request_metrics_enabled=False)
    database = Database(settings.database_url)
    run_migrations(database)

    with database.session_factory() as db:
        ready = research_objects.readiness(db)
        assert ready["model_execution_by_core"] is False
        assert ready["graph_native"] is True
        assert len(ready["object_types"]) == 8

        project = research_objects.create_object(
            db,
            object_type="research-project",
            name="Release validation project",
            slug="release-validation-project",
            description="v2.30.0 release validator",
            entity_id=None,
            visibility="public",
            entity_status="active",
            attributes={"research_question": "Can the model foundation preserve governed lineage?"},
            metadata={"validator": "v2.30.0"},
            release="2.30.0",
        )
        model = research_objects.create_object(
            db,
            object_type="model",
            name="Release validation model",
            slug="release-validation-model",
            description=None,
            entity_id=None,
            visibility="public",
            entity_status="active",
            attributes={
                "project_entity_id": project["id"],
                "model_kind": "mathematical",
                "execution_target": "workbench",
                "specification": {"equation": "y = ax + b"},
            },
            metadata={},
            release="2.30.0",
        )
        version = research_objects.create_object(
            db,
            object_type="model-version",
            name="Release validation model v1",
            slug="release-validation-model-v1",
            description=None,
            entity_id=None,
            visibility="public",
            entity_status="active",
            attributes={"model_entity_id": model["id"], "version_label": "1.0.0", "specification": {"equation": "y = ax + b"}},
            metadata={},
            release="2.30.0",
        )
        scenario = research_objects.create_object(
            db,
            object_type="scenario",
            name="Baseline",
            slug="baseline",
            description=None,
            entity_id=None,
            visibility="public",
            entity_status="active",
            attributes={"project_entity_id": project["id"], "scenario_state": "ready"},
            metadata={},
            release="2.30.0",
        )
        run = research_objects.create_object(
            db,
            object_type="model-run",
            name="Validation run",
            slug="validation-run",
            description=None,
            entity_id=None,
            visibility="public",
            entity_status="active",
            attributes={"model_version_entity_id": version["id"], "scenario_entity_id": scenario["id"], "executor_product": "workbench"},
            metadata={},
            release="2.30.0",
        )
        result = research_objects.create_object(
            db,
            object_type="result",
            name="Validation result",
            slug="validation-result",
            description=None,
            entity_id=None,
            visibility="public",
            entity_status="active",
            attributes={"model_run_entity_id": run["id"], "value": {"y": 3.0}},
            metadata={},
            release="2.30.0",
        )
        bundle = research_objects.project_bundle(db, project["id"])
        assert bundle["total_objects"] == 6
        assert result["attributes"]["model_run_entity_id"] == run["id"]
        assert version["attributes"]["immutable"] is True
        assert len(version["attributes"]["specification_hash"]) == 64

    status = migration_status(database)
    assert "0031" in status["applied"] and not status["pending"]
    assert status["research_projects"] == 1
    assert status["research_models"] == 1
    assert status["research_model_versions"] == 1
    assert status["research_scenarios"] == 1
    assert status["research_model_runs"] == 1
    assert status["research_results"] == 1

    print({
        "version": "2.30.0",
        "migration_0031_applied": True,
        "object_types": 8,
        "graph_native": True,
        "model_execution_by_core": False,
        "automatic_truth_promotion": False,
    })
    print("PASS - Core 2.30.0 Research Object & Model Foundation validation")
