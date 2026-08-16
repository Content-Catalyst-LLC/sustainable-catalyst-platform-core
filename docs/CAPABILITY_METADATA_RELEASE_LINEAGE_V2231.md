# Capability Metadata, Documentation & Release-Lineage Repair — v2.23.1

Core v2.23.1 repairs release truth without changing database schema or the v2.23.0 Federated Core execution model.

## Repair boundary

- Core runtime version becomes `2.23.1`.
- Migration head remains `0026`.
- No `0027` migration is added.
- No evidence, graph, governance, preservation, federation, connector, storage, or public API semantics are expanded.
- v2.23.0 trusted-node exchange remains reference-first and pull-oriented.
- Trust secrets remain runtime-only.
- Automatic truth promotion, ownership transfer, cross-node delivery, remote governance replication, and local-subject overwrite remain disabled.

## Capability truth repair

Two entries in `/v1/meta.deferred_capabilities` were stale:

| Capability | Implementation evidence | Correct state |
| --- | --- | --- |
| `distributed_connector_workers` | v2.9.0 persistent connector work queue, database-backed worker leases, retry/dead-letter handling, and `backend/scripts/run_connector_worker.py` | implemented |
| `server_sent_live_data_events` | v2.9.0 internal/public `StreamingResponse` endpoints with `text/event-stream` and regression coverage | implemented |

v2.23.1 moves both entries into the implemented `capabilities` set.

## Remaining deferred capability boundary

The following remain deferred because Core does not yet provide the complete named capability:

- `large_scale_graph_database_adapter`
- `user_casebooks`
- `external_public_key_signature_verification`
- `qualified_electronic_signatures`
- `external_snapshot_object_storage_adapter`
- `developer_self_service_billing`
- `distributed_rate_limit_backend`
- `scientific_object_storage_adapter`
- `native_raster_processing_workers`
- `native_scientific_file_parsers`

## Regression gates

`test_capability_metadata_release_lineage_v2231.py` requires:

1. implemented and deferred capability lists to be duplicate-free;
2. implemented and deferred capability sets to be disjoint;
3. the two v2.9.0 capabilities above to remain implemented;
4. static implementation evidence for SSE and leased connector workers to remain present;
5. migration head to remain `0026` for this repair release;
6. current runtime, SDK, WordPress, README, and roadmap versions to remain aligned.

The release validator repeats these checks before packaging or promotion.
