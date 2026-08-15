# Incident Response, Change Control & Rollback Coordination — v2.19.0

Core v2.19.0 turns observability signals into governed operational records without allowing telemetry to rewrite evidence or automatically mutate deployments. Operational incidents are internal/private/restricted records. Their events are append-only and hash-linked. High/critical changes require explicit approval by default. Rollback assessment is correlation-based and can recommend operator review, but `automatic_execution` and causal attribution are both hard-disabled in this release.

Public status is aggregate only: open incident counts, severity totals, active changes, and rollback execution policy. It exposes no incident titles, IDs, source references, operator names, notes, or change details.
