from __future__ import annotations

import tempfile
from pathlib import Path

from app.config import Settings
from app.database import Database
from app.migrations import migration_status, run_migrations
from app.services import research_objects, visual_reasoning

with tempfile.TemporaryDirectory() as td:
    db_path = Path(td) / "core.db"
    settings = Settings(database_url=f"sqlite:///{db_path}", observability_request_metrics_enabled=False)
    database = Database(settings.database_url)
    run_migrations(database)

    with database.session_factory() as db:
        ready = visual_reasoning.readiness(db)
        assert ready["graph_native"] is True
        assert ready["renderer_neutral"] is True
        assert ready["renderer_registry_in_core"] is True
        assert ready["layout_engine_in_core"] is False
        assert ready["automatic_truth_promotion"] is False

        project = research_objects.create_object(
            db,
            object_type="research-project",
            name="Visual release validation project",
            slug="visual-release-validation-project",
            description="v2.32.0 visual reasoning release validator",
            entity_id=None,
            visibility="public",
            entity_status="active",
            attributes={"research_question": "Can semantic visual reasoning preserve governed lineage?"},
            metadata={"validator": "v2.32.0"},
            release="2.32.0",
        )
        model = research_objects.create_object(
            db,
            object_type="model",
            name="Visual release validation model",
            slug="visual-release-validation-model",
            description=None,
            entity_id=None,
            visibility="public",
            entity_status="active",
            attributes={"project_entity_id": project["id"], "model_kind": "conceptual", "execution_target": "not-executable"},
            metadata={},
            release="2.32.0",
        )
        visual = visual_reasoning.create_object(
            db,
            name="Release validation system map",
            slug="release-validation-system-map",
            description=None,
            entity_id=None,
            visibility="public",
            entity_status="active",
            visual_kind="system-map",
            reasoning_purpose="explain",
            semantic_state="draft",
            coordinate_space="abstract",
            project_entity_id=project["id"],
            primary_subject_entity_id=model["id"],
            lens={"focus": "structure"},
            filters={},
            assumptions=["semantic model before renderer"],
            metadata={"validator": "v2.32.0"},
            release="2.32.0",
        )
        a = visual_reasoning.add_element(db, visual["id"], {
            "element_key": "project", "element_kind": "node", "semantic_role": "context",
            "label": "Research project", "source_entity_id": project["id"],
        })
        b = visual_reasoning.add_element(db, visual["id"], {
            "element_key": "model", "element_kind": "node", "semantic_role": "model",
            "label": "Research model", "source_entity_id": model["id"],
        })
        visual_reasoning.add_relation(db, visual["id"], {
            "source_element_id": a["id"], "target_element_id": b["id"],
            "relation_kind": "dependency", "direction": "directed", "confidence": 1.0,
        })
        visual_reasoning.add_layer(db, visual["id"], {
            "layer_key": "model", "name": "Model", "layer_kind": "model",
        })
        visual_reasoning.add_annotation(db, visual["id"], {
            "element_id": b["id"], "annotation_kind": "caveat",
            "text": "Renderer-neutral semantic object; no layout is executed by Core.",
        })
        snapshot = visual_reasoning.create_snapshot(
            db, visual["id"], snapshot_key="release-v1", created_by="validator", provenance={"release": "2.32.0"}
        )
        bundle = visual_reasoning.bundle(db, visual["id"])
        assert len(bundle["elements"]) == 2
        assert len(bundle["relations"]) == 1
        assert len(bundle["layers"]) == 1
        assert len(bundle["annotations"]) == 1
        assert len(bundle["snapshots"]) == 1
        assert len(snapshot["state_hash"]) == 64
        assert bundle["renderer_contract"]["renderer_neutral"] is True
        assert bundle["renderer_contract"]["layout_engine_in_core"] is False

    status = migration_status(database)
    assert "0032" in status["applied"] and not status["pending"]
    assert status["visual_reasoning_objects"] == 1
    assert status["visual_reasoning_elements"] == 2
    assert status["visual_reasoning_relations"] == 1
    assert status["visual_reasoning_layers"] == 1
    assert status["visual_reasoning_annotations"] == 1
    assert status["visual_reasoning_snapshots"] == 1

    print({
        "version": "2.32.0",
        "migration_0032_applied": True,
        "graph_native": True,
        "renderer_neutral": True,
        "renderer_registry_in_core": True,
        "layout_engine_in_core": False,
        "automatic_truth_promotion": False,
    })
    print("PASS - Core 2.32.0 Visual Reasoning Object Model validation")
