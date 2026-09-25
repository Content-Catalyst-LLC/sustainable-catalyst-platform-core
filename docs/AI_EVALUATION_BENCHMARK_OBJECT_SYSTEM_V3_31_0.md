# Platform Core v3.31.0 — AI Evaluation & Benchmark Object System

Contract: `sc.core.ai-evaluation-benchmark.v1`

Adds governed benchmark identity/versioning, exact evaluation dataset and ground-truth bindings, metric definitions, evaluation cases, case-level results, aggregate metrics, evaluation runs, benchmark results, confidence intervals, and descriptive cross-model comparison.

Research Lab executes evaluation workflows. Workspace/runtime providers execute computational jobs. Platform Core owns evaluation semantics, lineage, provenance and exchange contracts.

Core does not select a winning model, certify model quality, or declare scientific truth.

Provenance chain:

AIModelVersion → BenchmarkDefinition → DatasetVersion + Ground Truth → EvaluationCase → AIInferenceRun / AIArtifact → EvaluationMetricResult → EvaluationRun → BenchmarkResult → ModelBenchmarkComparison

Next: Platform Core v3.32.0 — AI Experiment & Reproducibility Packages.
