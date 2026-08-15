# v2.15.0 Distributed Processing, Storage & Scale Audit

## Boundaries
- Scaling mechanics do not change evidence authority, reconciliation, or provenance.
- Durable job/partition parameters strip credential-like keys before persistence.
- Large results require an explicit external URI once the inline byte limit is exceeded.
- External blob storage is optional and no paid provider is required.
- Backpressure blocks new work at active-job limits but never blocks workers from draining queued partitions.
- Retention compaction removes inline payloads while retaining hashes and metadata.
