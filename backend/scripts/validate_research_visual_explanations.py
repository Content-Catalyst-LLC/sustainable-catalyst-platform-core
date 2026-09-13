#!/usr/bin/env python3
import json
import os
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.models import Entity

with tempfile.TemporaryDirectory(prefix="sc-core-v2390-") as tmp:
    db_path = Path(tmp) / "validate.db"
    app = create_app(Settings(database_url=f"sqlite:///{db_path}", version="2.39.0"))
    with app.state.database.session_factory() as db:
        db.add(Entity(id="project:v2390", entity_type="research-project", slug="v2390", name="v2.39 validation", visibility="public")); db.commit()
    client = TestClient(app)
    health = client.get("/health").json(); assert health["version"] == "2.39.0" and health["research_librarian_visual_explanation"] is True
    ready = client.get("/v1/research-visual-explanations/readiness").json(); assert ready["migration_0043_applied"] is True
    created = client.post("/v1/research-visual-explanations", json={"data": {"project_entity_id": "project:v2390", "explanation_key": "validation", "name": "Validation", "visibility": "public"}})
    assert created.status_code == 200, created.text
    explanation_id = created.json()["id"]
    claim = client.post(f"/v1/research-visual-explanations/{explanation_id}/nodes", json={"data": {"node_key": "claim", "node_kind": "claim", "label": "Claim", "citation_required": True}}).json()
    cite = client.post(f"/v1/research-visual-explanations/{explanation_id}/citations", json={"data": {"citation_key": "source", "node_id": claim["id"], "external_uri": "https://example.org/source", "locator": {"section": "validation"}}})
    assert cite.status_code == 200, cite.text
    spec = client.get(f"/v1/research-visual-explanations/{explanation_id}/visualization").json()
    assert spec["contract"] == "sc.research-librarian-visual-explanation.v1" and spec["coverage"]["coverage_complete"] is True
    assert spec["source_retrieval_by_core"] is False and spec["natural_language_generation_by_core"] is False and spec["renderer_execution_by_core"] is False
print("PASS - Platform Core v2.39.0 Research Librarian Visual Explanation runtime validation")
