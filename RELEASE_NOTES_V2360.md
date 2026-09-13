# Platform Core v2.36.0 — Uncertainty, Sensitivity & Ensemble Reasoning

Release date: 2026-09-13

Adds migration `0039` and a governed reasoning layer for uncertainty definitions, sensitivity studies, and ensembles. Core stores assumptions, bounds/distribution metadata, parameter-factor bindings, externally supplied sensitivity metrics, ensemble membership, externally supplied statistics, provenance, validation, and renderer-neutral visualization specifications. Lab/Workbench/external runtimes remain responsible for sampling and numerical calculation.

## Explicit non-capabilities

Core does not generate Monte Carlo samples, calculate Sobol/Morris/correlation metrics, aggregate ensembles, fit distributions, infer probabilities, rank outcomes automatically, or promote outputs to truth.
