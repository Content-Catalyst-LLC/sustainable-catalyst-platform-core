# Capacity Forecasting & Resource Governance — v2.24.0

## Purpose
v2.24.0 makes capacity a first-class governed evidence domain inside Platform Core. It records what bounded resource is being observed, how much is being used or demanded, what trend is supported by recent observations, and what an operator-facing governance decision should be.

## Resource profiles
Profiles are provider-neutral and can describe processing jobs, queue depth, connector backlog, storage bytes, request throughput, compute units, or product-specific resources. Each profile declares a capacity limit, unit, warning threshold, critical threshold, forecast horizon, product scope, and public-summary flag.

## Forecast semantics
The first forecast method is `bounded-linear`. It uses a bounded observation window and exposes the number of observations, slope per hour, current value, predicted value, predicted utilization, hours-to-capacity when meaningful, confidence, and one of four states: `insufficient-data`, `stable`, `warning`, or `critical`.

Forecast confidence is an operational fit signal, not a statistical guarantee. Forecast records explicitly state that automatic scaling and infrastructure purchasing are disabled.

## Resource budgets
Budgets can apply across a resource type or to a specific product/resource key. `advisory` and `soft-limit` modes are supported. A soft-limit result records an `advisory-soft-block` decision but does not reject work or mutate another service.

## Runtime observations
`POST /v1/capacity/runtime/observe` creates/updates managed profiles and records current Core pressure for:
- active distributed processing jobs;
- queued processing partitions;
- pending/leased connector work items.

Additional storage, request-throughput, or product-specific observations can be posted through the generic profile/observation APIs.

## Certification
`SC_CORE_CERTIFICATION_REQUIRE_CAPACITY_READY=false` by default. When enabled, certification requires enabled profiles to have enough observations, a generated non-insufficient forecast, and zero critical forecasts. This is a release gate only; it does not auto-scale infrastructure.

## Public boundary
`GET /api/v1/capacity/status` exposes aggregate state, profile counts, forecast coverage, and warning/critical counts. It does not expose raw capacity limits, forecast values, budgets, or governance decision details.

## Explicit non-goals
Core does not buy infrastructure, change cloud plans, scale deployments, reallocate resources, enforce hard admission control, or claim forecasts are future truth. Those controls remain operator-governed and later release lines may add separately bounded admission-control infrastructure.
