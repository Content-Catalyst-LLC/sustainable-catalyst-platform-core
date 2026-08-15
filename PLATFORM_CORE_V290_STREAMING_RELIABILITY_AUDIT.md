# Core v2.9.0 Streaming & Reliability Audit

Release scope: persistent work queue, SSE, alerts, geographic subscriptions, stale-source detection, dead letters, replay, and explicit provider failover.

Validation requirements:

- migration `0012` applied with no pending migration;
- v2.9.0 reliability regression suite green;
- inherited Core regression groups green;
- public stream excludes non-public events;
- failover requires an explicit provider group;
- automatic worker failover additionally requires explicit parameter compatibility;
- external provider uptime remains non-blocking for release promotion;
- repository manifest and release-component SHA-256 hashes verify after clean extraction.
