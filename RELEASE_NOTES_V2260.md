# Platform Core v2.26.0 — Distributed Quotas, Admission Control & Workload Governance

- Adds migration `0029` for database-shared quota state, workload classes, admission decisions, and expiring concurrency leases.
- Adds per-subject quotas, burst budgets, priority classes, weighted fairness metadata, idempotent admission decisions, retry guidance, and hard reject/throttle outcomes.
- Admission can account for Platform Core SLO state and v2.24 capacity-governance state.
- Promotes the prior `distributed_rate_limit_backend` deferred capability to a portable database-shared implementation.
- Public status remains aggregate and does not expose quota limits or subject usage.
- Automatic scaling, infrastructure purchasing, and deployment mutation remain outside Core.
