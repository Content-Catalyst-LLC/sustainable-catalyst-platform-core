# Platform Core v2.34.0 — Interactive Model Canvas

Release v2.34.0 adds migration `0037` and a governed Interactive Model Canvas layer over the v2.28 Research Object & Model Foundation, v2.29 Visual Reasoning Object Model, and v2.30 Visualization Specification & Renderer Registry.

## Added

- `ModelCanvasRecord` bound to an existing research project and research model, with optional immutable model-version binding.
- Governed canvas nodes for model, component, input, parameter, variable, state, equation, scenario, run, result, output, and note semantics.
- Directed dependency/flow/causal/derived/parameterization/production/containment/requirement/association edges.
- Parameter/scenario controls with explicit external execution-handoff contracts.
- Immutable interaction states with deterministic SHA-256 state hashes.
- Saved canvas views and renderer-neutral diagram/composite/network visualization-specification compilation.
- Internal and public-safe APIs, Python/JavaScript SDK helpers, WordPress status, schemas, tests, and deployment tooling.

## Architectural boundaries

Platform Core does not execute numerical models, perform numerical computation, execute UI controls, calculate graphical layout, or promote canvas state/output to truth. Lab, Workbench, or another explicit execution service remains responsible for computation.

## Migration

`0037` — Interactive Model Canvas.
