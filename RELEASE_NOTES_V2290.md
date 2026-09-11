# Platform Core v2.29.0 — Visual Reasoning Object Model

Release date: 2026-09-11

## Summary

v2.29.0 adds a graph-native, renderer-neutral Visual Reasoning Object Model on top of the v2.28.0 Research Object & Model Foundation.

## Added

- migration `0032`;
- Universal Entity Registry backed `visual-reasoning-object` records;
- semantic visual elements with Core-entity and scientific-object source bindings;
- semantic visual relations with direction, magnitude, confidence, uncertainty, and provenance;
- reasoning layers for context, data, model, scenario, evidence, uncertainty, and annotation;
- governed annotations for claims, caveats, assumptions, uncertainty, provenance, and decisions;
- immutable semantic snapshots hashed with SHA-256;
- public-safe visual reasoning metadata endpoints;
- Python and JavaScript SDK helpers;
- WordPress `[sc_platform_core_visual_reasoning_status]` surface;
- full release validation, regression coverage, Mac promotion tooling, and VPS deployment commands.

## Boundaries

Platform Core does not render, select renderers, calculate layout, infer causality, or promote model output to truth. v2.30.0 is reserved for Visualization Specification & Renderer Registry.
