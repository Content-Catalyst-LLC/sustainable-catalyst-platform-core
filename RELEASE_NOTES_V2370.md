# Platform Core v2.37.0 — Causal Systems Explorer

## Summary
Adds a governed causal-reasoning layer on top of the research object model, visual reasoning, scenario compute, and uncertainty stack.

## New persistence
Migration 0041 creates causal_graphs, causal_variables, causal_edges, causal_interventions, causal_identifications, causal_estimates, and causal_diagnostics. The migration is additive and does not alter v2.36 uncertainty tables.

## Reasoning boundary
Core validates directed acyclic graph structure, traces directed paths, and generates conservative structural adjustment candidates. Identification claims remain explicit analyst/method records. Effect estimates and diagnostics require attributable provenance. Arbitrary model execution and automatic truth promotion remain outside Core.

## Integrations
Lab, Workbench, or external runtimes can receive explicit estimation handoff manifests for backdoor adjustment, IV, DiD, regression discontinuity, matching/weighting, g-formula, structural-equation, Bayesian, and custom methods.
