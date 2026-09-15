# v2.60.0 Reproducible Predictive Intelligence Packages Audit

The release is additive to v2.59.0 and preserves the non-executing Platform Core architecture. Seven new persistence families capture package identity, components, artifacts, environments, verification evidence, review evidence, and immutable snapshots.

A package may reference governed predictive objects from the model, backtest, calibration, ensemble/comparison, monitoring, spatial-temporal, causal-predictive, and predictive-decision layers. Governed component references are checked against the package project. External references remain allowed when provenance is explicit.

Snapshots are SHA-256 hashes of the complete package bundle excluding earlier snapshots, and each revision records the previous snapshot hash.

No execution, fitting, forecast regeneration, automatic replay, ranking, optimization, intervention, or truth promotion is introduced.
