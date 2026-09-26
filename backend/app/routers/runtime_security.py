from fastapi import APIRouter

from ..services.runtime_security_governance import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    GovernanceApproval,
    RuntimeSecurityGovernanceBundle,
    RuntimeSecurityPolicy,
    RuntimeSecurityRequest,
    contract_document,
    evaluate_security_request,
    reference_runtime_security_governance_bundle,
    to_scientific_security_artifact,
)

router = APIRouter(
    prefix="/api/v1/runtime-security",
    tags=["runtime-security"],
)
public_router = APIRouter(
    prefix="/public/v1/runtime-security",
    tags=["public-runtime-security"],
)


@router.get("/contract")
def get_contract():
    return contract_document()


@public_router.get("/contract")
def get_public_contract():
    return contract_document()


@router.get("/reference")
def get_reference():
    bundle = reference_runtime_security_governance_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "bundle": bundle.model_dump(mode="json", exclude_none=True),
        "bundle_fingerprint_sha256": bundle.fingerprint(),
        "record_fingerprints": {
            item.governance_record_id: item.fingerprint()
            for item in bundle.records
        },
    }


@router.post("/evaluate")
def evaluate(body: dict):
    policy = RuntimeSecurityPolicy.model_validate(body["policy"])
    request = RuntimeSecurityRequest.model_validate(body["request"])
    approval = None
    if body.get("approval") is not None:
        approval = GovernanceApproval.model_validate(body["approval"])
    decision = evaluate_security_request(
        policy=policy,
        request=request,
        approval=approval,
        decision_id=body.get("decision_id"),
    )
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "decision": decision.model_dump(mode="json", exclude_none=True),
        "decision_fingerprint_sha256": decision.fingerprint(),
    }


@router.post("/validate-policy")
def validate_policy(body: RuntimeSecurityPolicy):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "policy_fingerprint_sha256": body.fingerprint(),
    }


@router.post("/validate-bundle")
def validate_bundle(body: RuntimeSecurityGovernanceBundle):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "bundle_fingerprint_sha256": body.fingerprint(),
    }


@router.post("/scientific-artifact")
def scientific_artifact(body: RuntimeSecurityGovernanceBundle):
    payload = to_scientific_security_artifact(body)
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "scientific_artifact": payload,
    }
