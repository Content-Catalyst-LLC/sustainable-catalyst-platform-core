# Platform Core v3.3.0 — Statistical Reasoning Object Model

Platform Core v3.3.0 turns statistical evidence into first-class governed Core objects. It integrates Catalyst Analytics R v2.2.0 statistical diagnostics through Workspace v3.9.1 while keeping computation outside Core.

## Adds
- statistical reasoning objects bound explicitly to v3.2 analytical results
- diagnostic evidence, assumptions, robustness evidence, and model-comparison evidence
- coefficients and interval objects
- human-authored interpretation records with provenance
- immutable statistical reasoning snapshots
- ingestion for `sc.analytics-r.statistical-diagnostics-validation.v1`
- public read-only readiness and reasoning bundles

## Boundaries
Core does not infer statistical significance, certify scientific validity, select a preferred model, infer causality, rank models, or determine truth. P-values and thresholds remain evidence requiring contextual human interpretation.
