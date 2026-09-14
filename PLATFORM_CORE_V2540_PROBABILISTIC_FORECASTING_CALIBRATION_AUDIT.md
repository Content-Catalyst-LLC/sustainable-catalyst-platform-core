# Platform Core v2.54.0 Audit — Probabilistic Forecasting & Calibration

## Object model

Migration 0058 adds six additive tables: probabilistic forecasts, calibration studies, calibration bins, calibration mappings, probabilistic evaluations, and reproducible calibration packages. Existing v2.52 and v2.53 predictive tables are preserved.

## Validation invariants

Probabilities are bounded to [0,1], categorical probabilities sum to 1, quantile values are monotone by quantile, prediction intervals have ordered bounds, and probabilistic forecasts bind to exactly one forecast run or backtest fold. Calibration mappings and metric evidence are explicitly external.

## Provenance and reproduction

Calibration packages freeze the study, target, bins, mapping metadata, evaluation evidence, environment metadata, and governance boundaries into deterministic SHA-256 state with revision chaining.

## Execution boundary

Core remains registry/orchestration/provenance infrastructure. It does not execute model fitting, probabilistic inference, recalibration fitting/application, scoring-rule computation, calibration-metric computation, automated model ranking, or truth promotion.
