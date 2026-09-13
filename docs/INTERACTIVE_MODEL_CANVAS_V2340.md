# Platform Core v2.34.0 Interactive Model Canvas Audit

## Purpose

Provide a governed, renderer-neutral representation of interactive research-model canvases without moving numerical execution into Platform Core.

## Object model

- ModelCanvasRecord
- ModelCanvasNodeRecord
- ModelCanvasEdgeRecord
- ModelCanvasControlRecord
- ModelCanvasStateRecord
- ModelCanvasViewRecord

All canvases reuse the v2.28 research model foundation. Model/variable/parameter/scenario bindings are validated against the canvas project/model. Saved states are immutable and SHA-256 hashed.

## Execution boundary

Canvas controls express intent and external handoffs only. `execute_by_core=true` is rejected. Core records structure, control metadata, provenance, state and visualization contracts; Lab/Workbench/external runtimes execute models.

## Rendering boundary

The model canvas compiles to the v2.30 visualization specification registry. `model-canvas + diagram` resolves to the D3 renderer contract. Core does not execute D3 or calculate layout.

## Validation

Release-critical test line: 57/57 passing across v2.34, v2.33, v2.32, v2.31, v2.30, v2.29, v2.28, health, capability lineage and production certification.
