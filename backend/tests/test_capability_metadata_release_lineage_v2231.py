from __future__ import annotations

from pathlib import Path
from app.migrations import migration_status

PROMOTED_IMPLEMENTED = {"distributed_connector_workers", "server_sent_live_data_events"}


def test_v2231_capability_truth_remains_inherited(client):
    body = client.get('/v1/meta').json()
    assert body['version'] == '2.25.0'
    implemented = body['capabilities']
    deferred = body['deferred_capabilities']
    assert len(implemented) == len(set(implemented))
    assert len(deferred) == len(set(deferred))
    assert set(implemented).isdisjoint(deferred)
    assert PROMOTED_IMPLEMENTED <= set(implemented)
    assert PROMOTED_IMPLEMENTED.isdisjoint(deferred)


def test_v2231_promoted_capabilities_keep_runtime_proofs():
    root = Path(__file__).resolve().parents[2]
    router = (root / 'backend/app/routers/reliability.py').read_text()
    worker = (root / 'backend/scripts/run_connector_worker.py').read_text()
    service = (root / 'backend/app/services/reliability.py').read_text()
    assert 'StreamingResponse' in router and 'media_type="text/event-stream"' in router
    assert 'process_next_work' in worker
    assert 'claim_next_work' in service and 'lease_expires_at' in service


def test_v2231_migration_lineage_is_preserved_beneath_v2240(client):
    status = migration_status(client.app.state.database)
    assert status['pending'] == []
    assert '0026' in status['applied']
    assert status['applied'][-1] == '0028'


def test_v2231_historical_release_record_remains_present():
    root = Path(__file__).resolve().parents[2]
    roadmap = (root / 'docs/ROADMAP.md').read_text()
    assert 'v2.23.1 — Capability Metadata, Documentation & Release-Lineage Repair' in roadmap
    assert (root / 'RELEASE_NOTES_V2231.md').is_file()
