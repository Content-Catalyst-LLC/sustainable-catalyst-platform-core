from fastapi import APIRouter

from ..services.r_runtime_migration import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    AnalyticsRMigrationPlan,
    RRuntimeMigrationBundle,
    RRuntimeRegistration,
    contract_document,
    reference_r_runtime_migration,
)

router = APIRouter(
    prefix="/api/v1/r-runtime",
    tags=["r-runtime"],
)
public_router = APIRouter(
    prefix="/public/v1/r-runtime",
    tags=["public-r-runtime"],
)

@router.get("/contract")
def get_contract():
    return contract_document()

@public_router.get("/contract")
def get_public_contract():
    return contract_document()

@router.get("/reference")
def get_reference():
    bundle = reference_r_runtime_migration()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "bundle": bundle.model_dump(mode="json", exclude_none=True),
        "bundle_fingerprint_sha256": bundle.fingerprint(),
        "migration_plan_fingerprint_sha256": bundle.migration_plan.fingerprint(),
        "runtime_registration_fingerprint_sha256": (
            bundle.runtime_registration.fingerprint()
        ),
    }

@router.post("/validate-migration")
def validate_migration(body: AnalyticsRMigrationPlan):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "migration_plan_fingerprint_sha256": body.fingerprint(),
    }

@router.post("/validate-registration")
def validate_registration(body: RRuntimeRegistration):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "runtime_registration_fingerprint_sha256": body.fingerprint(),
    }

@router.post("/validate-bundle")
def validate_bundle(body: RRuntimeMigrationBundle):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "bundle_fingerprint_sha256": body.fingerprint(),
    }
