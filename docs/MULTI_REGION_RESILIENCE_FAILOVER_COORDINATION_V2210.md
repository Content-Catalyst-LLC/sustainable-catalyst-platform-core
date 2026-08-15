# Multi-Region Resilience & Failover Coordination — v2.21.0

Core v2.21.0 adds provider-neutral region/service health records, failover groups, replication-aware assessment, read-only degraded-mode recommendations, and operator-confirmed failover decision records.

## Safety contract

- Core does not execute cloud/provider failover commands.
- Automatic failover is disabled.
- Write failover requires a healthy/read-ready target, explicit write eligibility, and current replication within the configured lag threshold.
- When write safety is not proven, Core may recommend read-only degraded operation if configured.
- An operator must acknowledge and approve an actionable assessment before execution can be recorded.
- Region endpoints, evidence, and operator identities are not exposed on the public status API.
- Resilience records have no evidence authority and do not alter provenance or truth precedence.
