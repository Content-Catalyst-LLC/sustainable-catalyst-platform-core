# Platform Core v3.98.0 — Entity & Evidence Runtime Performance and Scale

## Purpose

v3.98.0 adds a governed performance-and-scale layer for the unified entity/evidence runtime. It defines how Core may accelerate, bound, queue, cache, batch, partition, benchmark, and degrade execution without changing the meaning or authority of governed research objects.

## Contract

`sc.core.entity-evidence-runtime-performance-scale.v1`

## Governed objects

- PerformanceScalePolicy
- RuntimePerformanceProfile
- ExecutionBudget
- CachePolicy
- GraphTraversalLimit
- BatchParallelismPolicy
- HighCardinalityEntityPolicy
- FederationQueuePolicy
- PackageSizeEnvelope
- BackpressureRule
- DegradationDecision
- ScaleBenchmarkResult
- PerformanceScaleTrace
- PerformanceScaleSnapshot

## Required boundaries

Performance optimizations preserve upstream contracts, epistemic states, validation states, and provenance. Silent sampling and silent truncation are prohibited. A cache hit is neither freshness proof nor content truth. Parallel workers do not create independent corroboration. Queue priority is operational priority only. A bounded or partial result cannot be interpreted as the complete evidence universe. Benchmarks measure runtime behavior, not truth or evidence strength. Degraded modes may preserve or reduce authority but may never increase it.

## Reference scale profile

The reference bundle contains four performance profiles, four execution budgets, three cache policies, three traversal limits, three batch policies, two high-cardinality policies, two federation queues, two package envelopes, three backpressure rules, three explicit degradation decisions, six reproducible scale benchmarks, two traces, and one immutable supersedable snapshot.

Database migration: none.
