# Platform Core v4.20.2 — Computational Provider Contract

Contract: `sc.core.computational-provider-contract.v1`

This compatibility release extends the v4.20.1 External Provider Registry with a provider-neutral computational execution/handoff contract. It defines computational provider profiles, capabilities, inputs, assumptions, environments, requests, results, cross-engine comparisons, provenance, and deterministic snapshots. External services bind to governed provider-registry identities; internal runtimes remain explicit internal references.

The contract preserves the legacy `sc.core.analytical-runtime-provider.v1` lineage. Core records and validates computational handoffs but does not execute computational providers, select providers autonomously, infer truth from computational output, automatically promote output to evidence, decide which engine is faulty when results disagree, or mutate governed graphs.

No database migration is introduced.
