# Platform Core v2.33.0 — Scenario Landscapes

Release v2.33.0 adds migration `0036` and a governed Scenario Landscapes layer over the v2.28 research scenario model, v2.29 visual reasoning, and v2.30 visualization specification registry.

Scenario Landscapes bind existing research scenarios into explicit comparison roles; define governed parameter/result/variable/metric dimensions; store externally supplied values, uncertainty intervals, provenance, and units; preserve saved comparison views; provide direct baseline-relative numeric summaries only when units match exactly; and compile renderer-neutral chart/composite/table specifications.

Core does not execute scenarios or models, infer values, convert units, rank alternatives, optimize choices, or promote scenario outputs to evidence/truth. Lab, Workbench, and explicitly configured external runtimes remain the compute boundary.
