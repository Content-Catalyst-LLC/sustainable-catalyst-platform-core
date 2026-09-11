# Platform Core v2.29.0 Visual Reasoning Object Model Audit

## Release assertion

The release adds semantic visual reasoning infrastructure without collapsing visualization, computation, evidence, or model execution into a single layer.

## Integrity controls

- visual objects inherit Core entity identity and visibility;
- project bindings must reference research projects;
- primary subjects and element source bindings must reference existing Core entities;
- scientific-object bindings must reference v2.27 stored-object records;
- relations cannot connect elements belonging to different visual objects;
- semantic snapshots are immutable keyed records with deterministic SHA-256 state hashes;
- public metadata follows parent entity visibility;
- no renderer, layout engine, or automatic truth promotion is enabled.

## Architecture boundary

Core owns semantic structure and lineage. Lab/Workbench own model execution. v2.30 owns renderer/specification contracts. Product UIs own concrete presentation and interaction.
