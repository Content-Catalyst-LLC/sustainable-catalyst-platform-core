# Platform Core v2.35.0 — Scenario Compute Engine

Platform Core v2.35.0 introduces a governed scenario-compute orchestration plane. It converts immutable research-model versions plus governed research scenarios into deterministic execution manifests and idempotent requests for Lab, Workbench, or approved external runtimes.

## Core owns

- reproducible scenario compute plans
- scenario case matrices and comparison roles
- parameter override and declared-bound validation
- deterministic SHA-256 case and request manifests
- idempotent execution requests
- external attempt/status records
- bindings to existing Research Model Run and Result objects
- public-safe readiness and metadata

## Core does not own

Core does not perform numerical model execution, arbitrary code execution, outbound runner dispatch, scenario optimization, or automatic truth promotion. Lab and Workbench remain the first-party numerical execution environments.
