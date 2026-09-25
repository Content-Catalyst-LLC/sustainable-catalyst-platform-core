# Platform Core v3.34.0 — AI Calibration, Drift & Risk Monitoring

## Objective

v3.34.0 adds governed calibration, drift and risk-monitoring semantics to the
Sustainable Catalyst AI Engineering stack.

Contract: `sc.core.ai-calibration-drift-risk.v1`

It answers:
- Are model probabilities calibrated against observed outcomes?
- Which exact evaluation/dataset/model version produced the calibration evidence?
- What changed between a reference window and a comparison window?
- Which drift method and thresholds were used?
- Which calibration, drift, robustness or operational signals create risk observations?
- Which monitoring policy governs the model version?
- What evidence is present in a point-in-time monitoring snapshot?

## First-class objects

- CalibrationBin
- CalibrationMetricResult
- CalibrationAssessment
- MonitoringWindow
- DriftSignalDefinition
- DriftObservation
- RiskIndicatorDefinition
- RiskObservation
- MonitoringPolicy
- MonitoringSnapshot
- CalibrationDriftRiskBundle

## Calibration

CalibrationAssessment binds exact AI model version, evaluation run, dataset
version and optional evaluation slice.

It supports reliability bins plus methods such as expected/max calibration
error, Brier score, log loss, isotonic calibration, Platt scaling, temperature
scaling and conformal approaches.

Core stores the evidence and thresholds; Research Lab executes calibration
analysis.

## Drift

MonitoringWindow makes comparison periods explicit and reproducible.

DriftSignalDefinition supports input, feature, label, prediction, probability,
embedding, retrieval, prompt, performance, latency and cost drift.

Supported method semantics include PSI, KS, chi-square, Jensen-Shannon,
KL divergence, Wasserstein distance, mean/variance shift, performance delta and
embedding distance.

DriftObservation binds the exact model version and baseline/comparison windows,
records observed/baseline values, delta, severity, threshold state and evidence.

## Risk monitoring

RiskIndicatorDefinition turns governed calibration, drift, robustness,
data-quality, operational, safety or governance signals into explicit monitoring
criteria.

RiskObservation records the observed evidence and risk level without granting
Core authority to block a model, retrain it, or certify safety.

MonitoringPolicy describes what should be watched, sample thresholds, retention
intent and an optional schedule hint. The hint is metadata only: Platform Core
does not run a background scheduler.

MonitoringSnapshot creates a reproducible point-in-time view joining:
- calibration evidence;
- drift observations;
- risk observations;
- v3.33 robustness runs;
- v3.33 error-analysis reports.

## Product boundaries

Research Lab:
- calibration analysis;
- drift experiments;
- robustness/risk analysis.

Workspace/runtime providers:
- computational execution.

Platform Core:
- calibration/drift/risk identity;
- monitoring policy contracts;
- provenance;
- cross-product exchange.

Core does not autonomously retrain, block or approve models.

## AI Engineering chain

v3.27 Model identity
→ v3.28 Training lineage
→ v3.29 Inference provenance
→ v3.30 Prompt/context/retrieval
→ v3.31 Evaluation/benchmarking
→ v3.32 Experiments/reproducibility
→ v3.33 Error analysis/robustness
→ v3.34 Calibration/drift/risk monitoring

Next: Platform Core v3.35.0 — Unified AI Research Object System.
