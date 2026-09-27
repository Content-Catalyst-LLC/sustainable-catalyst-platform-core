# Platform Core v3.64.0 — Neural Model Registry & Reproducible Model Packages

## Purpose

v3.64.0 closes the initial Platform Core neural-intelligence foundation by turning governed neural models into registry-addressable, portable research objects.

## Canonical lineage

`model specification -> training run -> checkpoint -> registry entry -> reproducibility manifest -> portable model package`

The package additionally binds inference plans, input/output schemas, immutable artifacts, runtime/environment requirements, evaluation and uncertainty objects, explainability/representation objects, intended use, and limitations.

## Core responsibilities

Platform Core defines and validates the registry and package contracts, lineage invariants, immutable artifact identities, governance metadata, deterministic fingerprints, intended use, and limitations.

## Compute boundary

Workspace, Research Lab, and authorized runtime providers train, evaluate, export, load, and execute models. Core does not install packages, download artifacts, execute model packages, run inference, select a best model, certify quality, or certify reproducibility.

## Governance

Registration is catalog/provenance state, not certification. A reproducible model package records what is required to attempt reproduction; it does not guarantee identical outcomes. A package or prediction is not evidence by itself.
