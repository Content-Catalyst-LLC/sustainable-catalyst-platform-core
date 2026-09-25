#!/usr/bin/env python3
from copy import deepcopy

from app.services.ai_calibration_drift_risk import (
    CONTRACT_VERSION,
    DriftSeverity,
    RiskLevel,
    contract_document,
    reference_calibration_drift_risk_bundle,
)

doc = contract_document()
assert doc["release"] == "3.34.0"
assert doc["contract"] == CONTRACT_VERSION
assert doc["capabilities"]["probability_calibration"] is True
assert doc["capabilities"]["data_and_prediction_drift"] is True
assert doc["capabilities"]["risk_indicators"] is True
assert doc["capabilities"]["monitoring_snapshots"] is True
assert doc["boundaries"]["core_executes_monitoring_jobs"] is False
assert doc["boundaries"]["core_autonomously_retrains_models"] is False

bundle = reference_calibration_drift_risk_bundle()
assert len(bundle.fingerprint()) == 64
assert bundle.fingerprint() == deepcopy(bundle).fingerprint()

calibration = bundle.calibration_assessments[0]
assert len(calibration.metric_results) == 2
assert any(item.passed is False for item in calibration.metric_results)

drift = bundle.drift_observations[0]
assert drift.threshold_exceeded is True
assert drift.severity == DriftSeverity.moderate
assert drift.delta == 0.12

policy = bundle.monitoring_policy
assert policy.schedule_hint == "daily"
assert policy.provenance["core_performs_scheduling"] is False

snapshot = bundle.monitoring_snapshots[0]
assert snapshot.overall_risk_level == RiskLevel.high
assert snapshot.robustness_run_refs
assert snapshot.error_analysis_report_refs

print("PASS - Platform Core v3.34.0 AI Calibration, Drift & Risk Monitoring")
print(f"CONTRACT={CONTRACT_VERSION}")
print("PROBABILITY_CALIBRATION=enabled")
print("MONITORING_WINDOWS=enabled")
print("DRIFT_SIGNALS=enabled")
print("DRIFT_SEVERITY=enabled")
print("RISK_INDICATORS=enabled")
print("MONITORING_POLICIES=enabled")
print("MONITORING_SNAPSHOTS=enabled")
print("V333_ROBUSTNESS_LINKS=enabled")
print("CORE_PERFORMS_BACKGROUND_SCHEDULING=false")
print("CORE_AUTONOMOUSLY_RETRAINS_MODELS=false")
print("CORE_EXECUTES_MONITORING_JOBS=false")
