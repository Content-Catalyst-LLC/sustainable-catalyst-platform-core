# Humanitarian Access & Essential Services Fabric — v2.11.0

Core v2.11.0 records humanitarian and essential-service conditions as source-aware observations. It does not infer normality from missing records and does not flatten distinct evidence into a crisis score.

## Evidence domains

Health, education, food, water, electricity, fuel, displacement, communications, shelter, humanitarian access, protection, and other governed conditions.

## Semantic roles

- `operational-condition` — a source reports an operational/service condition.
- `humanitarian-indicator` — a standardized humanitarian indicator.
- `classification` — a source-defined classification such as a food-security category.
- `structural-baseline` — a baseline/annual statistic that must not be presented as current service availability.
- `contextual-report` — report context that is not promoted to a structured operational claim.

## Source materialization boundary

HDX HAPI normalized observations are materialized only when the metric has an explicit semantic mapping. ReliefWeb report metadata is not automatically converted into a condition. Future connectors may opt in only through explicit `humanitarian_mapping` metadata or a governed adapter mapping.

## Interpretation safeguards

Core does not calculate a synthetic crisis-severity score, infer legal responsibility, infer causality, or interpret zero records as normal conditions. Facility linkage is optional and only used when the evidence identifies a facility.
