# Platform Core v2.61.0 — Visual Reasoning Runtime & Scene Graph

Adds a renderer-neutral runtime above the v2.29–v2.41 visual reasoning foundation. Migration 0065 introduces governed scenes, layers, nodes, edges, annotations, saved viewport/selection/interaction state, cross-product bindings, and immutable hash-chained scene snapshots.

Core remains non-rendering and non-inferential: layout, SVG/Canvas/WebGL rendering, animation, GPU execution, browser hit-testing, and visual inference stay outside Platform Core.
