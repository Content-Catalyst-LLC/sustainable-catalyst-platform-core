# Platform Core v2.35.0 Scenario Compute Engine Audit

## Release contract

- Migration: `0038`
- Core version: `2.35.0`
- New service: `backend/app/services/scenario_compute.py`
- New router: `/v1/scenario-compute` and public metadata under `/api/v1/scenario-compute`
- New WordPress shortcode: `[sc_platform_core_scenario_compute_status]`

## Architectural invariants

1. Existing research scenarios are reused; there is no duplicate scenario object model.
2. Immutable model versions are required for reproducible compute requests.
3. Parameter overrides are validated against model parameters and declared numeric bounds.
4. Input manifests and requests are SHA-256-addressed and idempotent.
5. Lab/Workbench/external runtimes execute numerical work; Core records requests and attempts only.
6. Existing Research Model Run and Result objects remain the canonical execution/result records.
7. Core does not perform arbitrary code execution, scenario optimization, network runner dispatch, or automatic truth promotion.
