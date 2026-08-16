# Platform Core v2.26.0 — Distributed Quotas, Admission Control & Workload Governance

v2.26.0 converts resource-governance warnings into an explicit, auditable workload admission control plane.

## Implemented

- database-shared quota policies and windowed usage buckets;
- exact-subject and wildcard quota matching;
- per-workload-class quota targeting;
- burst budgets;
- workload priority and queue-weight metadata;
- per-class concurrency limits enforced through expiring leases;
- request-unit limits;
- idempotent admission request keys;
- `allow`, `throttle`, and `reject` decisions;
- retry-after guidance;
- capacity-aware throttling using v2.24 resource governance state;
- SLO-aware throttling using v2.18 observability/SLO state;
- optional certification gating;
- aggregate public-safe status.

## Distributed-state boundary

The first distributed quota backend is the production database itself. Multiple Core processes sharing the same database share quota policy and usage state without requiring Redis or another proprietary service. The adapter boundary remains open for future external coordination backends if operating scale requires them.

## Safety / actuation boundary

v2.26.0 can make hard workload admission decisions. It does **not** autoscale infrastructure, purchase resources, mutate deployments, move workloads between regions, or infer product-level truth authority.
