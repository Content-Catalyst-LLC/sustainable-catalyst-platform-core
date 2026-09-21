# Platform Core v2.87.0 — Computation, Analysis & Execution Lineage

This layer records how externally executed computations connect to research inputs and downstream scholarly objects. It supports Python, R, Julia, SQL, Workbench, ML runtimes, containers, external services, notebooks, and other declared runtimes without making Platform Core the executor.

## Lineage chain
Protocol/method → versioned inputs → parameters/assumptions → software environment → declared execution steps → outputs → findings/claims/conclusions/publications.

## Boundaries
Core does not execute code, run specialist runtimes, transform data, compute statistics, fit/train models, generate outputs, infer findings/claims, validate results, infer reproducibility, or infer truth.
