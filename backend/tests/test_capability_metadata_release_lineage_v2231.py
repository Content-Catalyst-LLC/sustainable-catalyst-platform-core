from __future__ import annotations

from pathlib import Path

from app.migrations import migration_status


PROMOTED_IMPLEMENTED = {
    "distributed_connector_workers",
    "server_sent_live_data_events",
}


def test_v2231_meta_capability_sets_are_truthful_and_disjoint(client):
    response = client.get("/v1/meta")
    assert response.status_code == 200
    body = response.json()
    assert body["version"] == "2.23.1"

    implemented = body["capabilities"]
    deferred = body["deferred_capabilities"]
    assert len(implemented) == len(set(implemented))
    assert len(deferred) == len(set(deferred))
    assert set(implemented).isdisjoint(deferred)
    assert PROMOTED_IMPLEMENTED <= set(implemented)
    assert PROMOTED_IMPLEMENTED.isdisjoint(deferred)


def test_v2231_promoted_capabilities_have_runtime_implementation_proofs():
    root = Path(__file__).resolve().parents[2]
    reliability_router = (root / "backend/app/routers/reliability.py").read_text()
    worker = (root / "backend/scripts/run_connector_worker.py").read_text()
    reliability_service = (root / "backend/app/services/reliability.py").read_text()

    assert "StreamingResponse" in reliability_router
    assert 'media_type="text/event-stream"' in reliability_router
    assert "/stream" in reliability_router
    assert "process_next_work" in worker
    assert "claim_next_work" in reliability_service
    assert "lease_expires_at" in reliability_service


def test_v2231_release_lineage_preserves_migration_head_0026(client):
    status = migration_status(client.app.state.database)
    assert status["pending"] == []
    assert status["applied"][-1] == "0026"
    assert "0027" not in status["applied"]


def test_v2231_current_release_surfaces_are_aligned():
    root = Path(__file__).resolve().parents[2]
    assert 'version: str = "2.23.1"' in (root / "backend/app/config.py").read_text()
    assert '"version": "2.23.1"' in (root / "backend/public_sdk/javascript/package.json").read_text()
    assert 'version = "2.23.1"' in (root / "backend/public_sdk/python/pyproject.toml").read_text()
    plugin = (root / "wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php").read_text()
    assert "Version: 2.23.1" in plugin
    assert "SCPC_VERSION', '2.23.1" in plugin
    assert (root / "README.md").read_text().startswith("# Sustainable Catalyst Platform Core v2.23.1")
    assert "v2.23.1 — Capability Metadata, Documentation & Release-Lineage Repair" in (root / "docs/ROADMAP.md").read_text()
