from fastapi import APIRouter
from ..services.ai_calibration_drift_risk import (
    CORE_RELEASE,
    CONTRACT_VERSION,
    CalibrationAssessment,
    MonitoringWindow,
    DriftSignalDefinition,
    DriftObservation,
    RiskIndicatorDefinition,
    RiskObservation,
    MonitoringPolicy,
    MonitoringSnapshot,
    CalibrationDriftRiskBundle,
    contract_document,
    reference_calibration_drift_risk_bundle,
)

router = APIRouter(
    prefix="/api/v1/ai-calibration-drift-risk",
    tags=["ai-calibration-drift-risk"],
)
public_router = APIRouter(
    prefix="/public/v1/ai-calibration-drift-risk",
    tags=["public-ai-calibration-drift-risk"],
)

@router.get("/contract")
def get_contract():
    return contract_document()

@public_router.get("/contract")
def get_public_contract():
    return contract_document()

@router.get("/reference")
def get_reference():
    bundle = reference_calibration_drift_risk_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "bundle": bundle.model_dump(mode="json", exclude_none=True),
        "bundle_fingerprint_sha256": bundle.fingerprint(),
        "monitoring_policy_fingerprint_sha256": bundle.monitoring_policy.fingerprint(),
        "monitoring_snapshot_fingerprints": {
            item.monitoring_snapshot_id: item.fingerprint()
            for item in bundle.monitoring_snapshots
        },
        "calibration_fingerprints": {
            item.calibration_assessment_id: item.fingerprint()
            for item in bundle.calibration_assessments
        },
        "drift_observation_fingerprints": {
            item.drift_observation_id: item.fingerprint()
            for item in bundle.drift_observations
        },
    }

@router.post("/validate-calibration")
def validate_calibration(body: CalibrationAssessment):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "calibration_fingerprint_sha256": body.fingerprint(),
    }

@router.post("/validate-window")
def validate_window(body: MonitoringWindow):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "monitoring_window_fingerprint_sha256": body.fingerprint(),
    }

@router.post("/validate-drift-signal")
def validate_drift_signal(body: DriftSignalDefinition):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "drift_signal_fingerprint_sha256": body.fingerprint(),
    }

@router.post("/validate-drift-observation")
def validate_drift_observation(body: DriftObservation):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "drift_observation_fingerprint_sha256": body.fingerprint(),
    }

@router.post("/validate-risk-indicator")
def validate_risk_indicator(body: RiskIndicatorDefinition):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "risk_indicator_fingerprint_sha256": body.fingerprint(),
    }

@router.post("/validate-risk-observation")
def validate_risk_observation(body: RiskObservation):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "risk_observation_fingerprint_sha256": body.fingerprint(),
    }

@router.post("/validate-monitoring-policy")
def validate_monitoring_policy(body: MonitoringPolicy):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "monitoring_policy_fingerprint_sha256": body.fingerprint(),
    }

@router.post("/validate-monitoring-snapshot")
def validate_monitoring_snapshot(body: MonitoringSnapshot):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "monitoring_snapshot_fingerprint_sha256": body.fingerprint(),
    }

@router.post("/validate-bundle")
def validate_bundle(body: CalibrationDriftRiskBundle):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "bundle_fingerprint_sha256": body.fingerprint(),
    }
