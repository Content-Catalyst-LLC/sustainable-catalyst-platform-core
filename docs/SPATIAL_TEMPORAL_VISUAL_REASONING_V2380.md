# Platform Core v2.38.0 — Spatial & Temporal Visual Reasoning

Platform Core governs spatial-temporal scenes, GeoJSON feature bindings, events/intervals, trajectories, change observations, saved views, provenance, and renderer-neutral map/timeline specifications.

## Execution boundary

Core validates semantics and compiles contracts. CRS reprojection, spatial joins, routing, raster processing, remote sensing, and arbitrary temporal models execute in Site Intelligence, Lab, Workbench, or another declared runtime. No computed result is automatically promoted to truth.
