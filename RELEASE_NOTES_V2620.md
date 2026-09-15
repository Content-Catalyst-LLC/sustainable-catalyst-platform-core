# Platform Core v2.62.0 — Interactive Renderer & View Composition

Adds renderer-neutral composition governance above the v2.61 scene graph: renderer profiles, view compositions, renderer assignments, linked-view groups, propagated interaction state, capability resolutions, and immutable composition snapshots.

Core coordinates view state and provenance. SVG/Canvas/WebGL drawing, layout algorithms, animation, browser hit-testing, GPU execution, and visual inference remain outside Core.

Migration: `0066`.
