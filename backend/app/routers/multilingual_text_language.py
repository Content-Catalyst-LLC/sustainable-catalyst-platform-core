from fastapi import APIRouter

from ..services.multilingual_text_language import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    CanonicalTextSource,
    LanguageIdentity,
    LanguageSpanBinding,
    MultilingualTextLanguageBundle,
    ScriptIdentity,
    TextSourceProvenanceRecord,
    TextUnitRecord,
    contract_document,
    reference_multilingual_text_language_bundle,
)

router = APIRouter(prefix="/api/v1/language-text", tags=["language-text"])
public_router = APIRouter(prefix="/public/v1/language-text", tags=["public-language-text"])


@router.get("/contract")
def get_contract():
    return contract_document()


@public_router.get("/contract")
def get_public_contract():
    return contract_document()


@router.get("/reference")
def get_reference():
    bundle = reference_multilingual_text_language_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "bundle": bundle.model_dump(mode="json", exclude_none=True),
        "bundle_fingerprint_sha256": bundle.fingerprint(),
    }


@router.post("/validate-language")
def validate_language(body: LanguageIdentity):
    return {"ok": True, "fingerprint_sha256": body.fingerprint()}


@router.post("/validate-script")
def validate_script(body: ScriptIdentity):
    return {"ok": True, "fingerprint_sha256": body.fingerprint()}


@router.post("/validate-provenance")
def validate_provenance(body: TextSourceProvenanceRecord):
    return {"ok": True, "fingerprint_sha256": body.fingerprint()}


@router.post("/validate-source")
def validate_source(body: CanonicalTextSource):
    return {"ok": True, "fingerprint_sha256": body.fingerprint()}


@router.post("/validate-text-unit")
def validate_text_unit(body: TextUnitRecord):
    return {"ok": True, "fingerprint_sha256": body.fingerprint()}


@router.post("/validate-language-span")
def validate_language_span(body: LanguageSpanBinding):
    return {"ok": True, "fingerprint_sha256": body.fingerprint()}


@router.post("/validate-bundle")
def validate_bundle(body: MultilingualTextLanguageBundle):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "bundle_fingerprint_sha256": body.fingerprint(),
    }
