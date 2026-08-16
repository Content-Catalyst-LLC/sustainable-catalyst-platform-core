# v2.26.0 Distributed Quota / Admission Audit

## Boundary
Core now makes enforceable workload admission decisions, but does not purchase infrastructure, scale deployments, or mutate deployment topology.

## Persistence
Migration 0029 adds workload classes, quota policies, shared usage buckets, admission decisions, and expiring leases. Shared quota state is portable database state and can be consumed by multiple Core instances using the same production database.

## Governance
Admission is idempotent by request key, auditable, supports hard rejection, retry-after guidance, burst budgets, class concurrency, and SLO/capacity-aware throttling.

## Public safety
The public surface exposes readiness and aggregate counts only; policy limits and per-subject usage are not published.
