# Platform Core v2.33.0 Scenario Landscapes Audit

- Migration: `0036`.
- Reuses first-class v2.28 `scenario` entities; no duplicate scenario model.
- One governed baseline per landscape; alternative/reference/stress/sensitivity roles supported.
- Explicit comparison dimensions may bind parameters, variables, or result entities.
- Values preserve units, lower/upper bounds, uncertainty metadata, provenance, and arbitrary JSON values.
- Baseline deltas are direct arithmetic only for numeric values with matching units; no conversion or ranking.
- Visualization specs compile through v2.30 renderer contracts.
- Scenario/model execution, optimization, ranking, unit conversion, and truth promotion remain outside Core.
