# Platform Core v2.61.0 — Visual Reasoning Runtime & Scene Graph

Platform Core v2.61.0 introduces a renderer-neutral runtime contract that turns the existing semantic visual object model into a durable scene graph.

## Core-owned state
- governed scenes bound to research projects and optional v2.29 visual objects
- ordered layers
- semantic nodes and edges with source/provenance bindings
- annotations
- saved viewport, selection, filter, layer, and interaction state
- cross-product bindings to Core, Library, Site Intelligence, Lab, Workbench, Decision Studio, predictive and forensic objects
- immutable, revisioned, hash-chained scene snapshots

## Runtime boundary
Core does not compute layout, render SVG/Canvas/WebGL, animate scenes, perform GPU work, hit-test browser geometry, or infer truth from visual form. Specialist clients/renderers consume the scene contract.

Contract: `sc.visual-runtime.scene.v1`.
