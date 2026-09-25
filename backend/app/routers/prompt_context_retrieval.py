from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ..services.prompt_context_retrieval import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    ContextAssembly,
    PromptTemplate,
    PromptVersion,
    PromptVersionBinding,
    RetrievalContextBundle,
    RetrievalQuery,
    RetrievalResultSet,
    RetrievedItem,
    contract_document,
    reference_prompt_context_retrieval,
)

router = APIRouter(
    prefix="/api/v1/prompt-context-retrieval",
    tags=["prompt-context-retrieval"],
)
public_router = APIRouter(
    prefix="/public/v1/prompt-context-retrieval",
    tags=["public-prompt-context-retrieval"],
)


@router.get("/contract")
def get_contract():
    return contract_document()


@public_router.get("/contract")
def get_public_contract():
    return contract_document()


@router.get("/reference")
def get_reference():
    bundle = reference_prompt_context_retrieval()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "bundle": bundle.model_dump(mode="json", exclude_none=True),
        "bundle_fingerprint_sha256": bundle.fingerprint(),
        "prompt_fingerprint_sha256": bundle.prompt_binding.prompt.fingerprint(),
        "prompt_version_fingerprint_sha256": (
            bundle.prompt_binding.prompt_version.fingerprint()
        ),
        "context_assembly_fingerprint_sha256": (
            bundle.context_assembly.fingerprint()
        ),
        "retrieval_query_fingerprints": {
            item.retrieval_query_id: item.fingerprint()
            for item in bundle.retrieval_queries
        },
        "retrieval_result_set_fingerprints": {
            item.retrieval_result_set_id: item.fingerprint()
            for item in bundle.retrieval_result_sets
        },
    }


@router.post("/validate-prompt")
def validate_prompt(body: PromptTemplate):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "prompt": body.model_dump(mode="json", exclude_none=True),
        "prompt_fingerprint_sha256": body.fingerprint(),
    }


@router.post("/validate-prompt-version")
def validate_prompt_version(body: PromptVersion):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "prompt_version": body.model_dump(mode="json", exclude_none=True),
        "prompt_version_fingerprint_sha256": body.fingerprint(),
    }


@router.post("/validate-prompt-binding")
def validate_prompt_binding(body: PromptVersionBinding):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "binding": body.model_dump(mode="json", exclude_none=True),
        "binding_fingerprint_sha256": body.fingerprint(),
    }


@router.post("/validate-retrieval-query")
def validate_retrieval_query(body: RetrievalQuery):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "retrieval_query": body.model_dump(mode="json", exclude_none=True),
        "retrieval_query_fingerprint_sha256": body.fingerprint(),
    }


@router.post("/validate-retrieval-result-set")
def validate_retrieval_result_set(body: RetrievalResultSet):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "retrieval_result_set": body.model_dump(mode="json", exclude_none=True),
        "retrieval_result_set_fingerprint_sha256": body.fingerprint(),
    }


@router.post("/validate-context-assembly")
def validate_context_assembly(body: ContextAssembly):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "context_assembly": body.model_dump(mode="json", exclude_none=True),
        "context_assembly_fingerprint_sha256": body.fingerprint(),
    }


@router.post("/validate-bundle")
def validate_bundle(body: RetrievalContextBundle):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "bundle": body.model_dump(mode="json", exclude_none=True),
        "bundle_fingerprint_sha256": body.fingerprint(),
    }
