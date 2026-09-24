# Platform Core v3.21.0 — Uncertainty & Probabilistic Evidence Integration

Adds a governed bridge from Catalyst Analytics R v2.3.0 uncertainty/sensitivity runtime outputs into Platform Core. The release records uncertainty studies, parameter/output distributions, probabilistic summaries, Sobol/Morris sensitivity evidence, ensemble evidence, human-authored interpretations, and immutable snapshots linked to existing analytical results and optional statistical-reasoning objects.

Core remains non-executing and non-certifying: uncertainty is evidence rather than truth; sensitivity does not establish causality; Core does not rank parameters, choose policy, optimize decisions, or certify scientific validity.

Migration: `0108`.
Contracts: `sc.core.uncertainty-probabilistic-evidence.v1` consumes `sc.analytics-r.uncertainty-sensitivity-runtime.v1`.
