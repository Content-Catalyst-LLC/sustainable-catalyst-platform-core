# Platform Core v2.28.0 — Research Object & Model Foundation

Released: 2026-09-11

This release adds the canonical research/model semantics needed for Sustainable Catalyst's next visual reasoning line.

## Added

- migration `0031`;
- graph-native Research Project, Model, Model Version, Variable, Parameter, Scenario, Model Run, and Result records;
- deterministic model specification hashing and immutable-version metadata;
- variable units/domain/uncertainty and parameter defaults/bounds/priors/sensitivity metadata;
- scenario assumptions and parameter assignments;
- model-run links to provenance activities and calculation traces;
- result links to v2.27 scientific stored objects;
- internal/public APIs and project bundles;
- registry statistics, Python/JavaScript SDK methods, WordPress status, JSON schemas, regression tests, and release validators.

## Explicit non-capabilities

- Core does not execute models.
- Core does not render visualizations.
- Core does not automatically promote model output to evidence or truth.
- Core does not infer or verify causal relationships merely because a model contains them.

## Next

v2.29.0 — Visual Reasoning Object Model.
