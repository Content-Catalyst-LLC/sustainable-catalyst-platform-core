from fastapi import APIRouter

from ..services.translation_alignment import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    DerivationProvenanceRecord,
    DerivedTextRepresentation,
    ParallelTextAlignmentRecord,
    RepresentationVariantSet,
    TranslationTransliterationAlignmentBundle,
    contract_document,
    reference_translation_alignment_bundle,
)

router = APIRouter(prefix="/api/v1/translation-alignments", tags=["translation-alignments"])
public_router = APIRouter(prefix="/public/v1/translation-alignments", tags=["public-translation-alignments"])


@router.get("/contract")
def get_contract():
    return contract_document()


@public_router.get("/contract")
def get_public_contract():
    return contract_document()


@router.get("/reference")
def get_reference():
    bundle = reference_translation_alignment_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "bundle": bundle.model_dump(mode="json", exclude_none=True),
        "bundle_fingerprint_sha256": bundle.fingerprint(),
    }


def _fingerprint(body):
    return {"ok": True, "fingerprint_sha256": body.fingerprint()}


@router.post("/validate-provenance")
def validate_provenance(body: DerivationProvenanceRecord):
    return _fingerprint(body)


@router.post("/validate-representation")
def validate_representation(body: DerivedTextRepresentation):
    return _fingerprint(body)


@router.post("/validate-alignment")
def validate_alignment(body: ParallelTextAlignmentRecord):
    return _fingerprint(body)


@router.post("/validate-variant-set")
def validate_variant_set(body: RepresentationVariantSet):
    return _fingerprint(body)


@router.post("/validate-bundle")
def validate_bundle(body: TranslationTransliterationAlignmentBundle):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "bundle_fingerprint_sha256": body.fingerprint(),
    }
