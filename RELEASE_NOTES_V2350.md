# Platform Core v2.35.0 — Scenario Compute Engine

Release 2.35.0 adds migration `0038` and the governed Scenario Compute Engine orchestration layer.

The release builds on v2.28 research objects, v2.33 Scenario Landscapes, and v2.34 Interactive Model Canvas. Compute plans require immutable model versions, bind cases to existing research scenarios, validate parameter overrides against declared model-parameter bounds, generate deterministic input manifests, create idempotent execution requests, record external Lab/Workbench execution attempts, and bind returned model runs/results.

Platform Core remains the orchestration and provenance plane: it does not numerically execute models, dispatch arbitrary network jobs, execute arbitrary code, optimize scenarios, or promote results to truth.
