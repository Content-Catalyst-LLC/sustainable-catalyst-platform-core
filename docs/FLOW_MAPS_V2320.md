# Platform Core v2.32.0 — Flow Maps

Flow Maps are governed `flow-map` visual reasoning objects. Nodes remain v2.29 semantic elements. Directed flows reuse v2.29 `relation_kind=flow` relations, while v2.32 adds channel, quantity, uncertainty, time, state-observation, view, validation, and balance metadata.

## Core responsibilities

Core persists semantic flow structure, provenance, uncertainty, explicit units, exact-unit balance summaries, and immutable visualization-specification handoffs.

## Explicit non-responsibilities

Core does not automatically convert units, execute simulations, infer conservation, choose physical equations, perform renderer/layout execution, or promote a flow structure to evidence/truth.

## Rendering handoff

`network` specifications resolve through the v2.30 registry to compatible external graph renderer contracts such as D3. `map` specifications can resolve to MapLibre-compatible contracts. Resolution is metadata only and never renderer execution.
