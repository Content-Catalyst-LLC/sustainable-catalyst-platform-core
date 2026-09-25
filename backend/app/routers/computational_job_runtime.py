from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.computational_job_runtime import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    ComputationalJob,
    JobTransitionRequest,
    build_dispatch_envelope,
    contract_document,
    reference_julia_job,
    transition_job,
    validate_job,
)
from ..services.execution_environment_provenance import (
    ExecutionEnvironmentProvenance,
)

router = APIRouter(
    prefix="/api/v1/computational-jobs",
    tags=["computational-jobs"],
)
public_router = APIRouter(
    prefix="/public/v1/computational-jobs",
    tags=["public-computational-jobs"],
)


class ValidateRequest(BaseModel):
    job: ComputationalJob
    observed_environment: ExecutionEnvironmentProvenance | None = None


class TransitionBody(BaseModel):
    job: ComputationalJob
    transition: JobTransitionRequest


@router.get("/contract")
def get_contract():
    return contract_document()


@public_router.get("/contract")
def get_public_contract():
    return contract_document()


@router.get("/reference/julia-v0.3.0")
def get_reference_job():
    job = reference_julia_job()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "job": job.model_dump(mode="json", exclude_none=True),
        "job_fingerprint_sha256": job.fingerprint(),
        "dispatch_envelope": build_dispatch_envelope(job).model_dump(
            mode="json", exclude_none=True
        ),
    }


@router.post("/validate")
def validate(body: ValidateRequest):
    report = validate_job(body.job, body.observed_environment)
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "validation": report.model_dump(mode="json", exclude_none=True),
    }


@router.post("/fingerprint")
def fingerprint(job: ComputationalJob):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "job_fingerprint_sha256": job.fingerprint(),
    }


@router.post("/dispatch-envelope")
def dispatch_envelope(job: ComputationalJob):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "dispatch_envelope": build_dispatch_envelope(job).model_dump(
            mode="json", exclude_none=True
        ),
    }


@router.post("/transition")
def transition(body: TransitionBody):
    try:
        job = transition_job(body.job, body.transition)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "job": job.model_dump(mode="json", exclude_none=True),
    }
