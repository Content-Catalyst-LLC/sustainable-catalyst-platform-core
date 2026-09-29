from fastapi import APIRouter

from ..services.linguistic_annotation import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    AnnotationProvenanceRecord,
    ConstituencyNode,
    ConstituencyParseRecord,
    DependencyParseRecord,
    DependencyRelation,
    LinguisticAnnotationBundle,
    MorphemeRecord,
    MorphologicalAnnotation,
    PartOfSpeechAnnotation,
    TokenRecord,
    TokenizationRecord,
    contract_document,
    reference_linguistic_annotation_bundle,
)

router = APIRouter(prefix="/api/v1/linguistic-annotations", tags=["linguistic-annotations"])
public_router = APIRouter(prefix="/public/v1/linguistic-annotations", tags=["public-linguistic-annotations"])


@router.get("/contract")
def get_contract():
    return contract_document()


@public_router.get("/contract")
def get_public_contract():
    return contract_document()


@router.get("/reference")
def get_reference():
    bundle = reference_linguistic_annotation_bundle()
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
def validate_provenance(body: AnnotationProvenanceRecord):
    return _fingerprint(body)


@router.post("/validate-tokenization")
def validate_tokenization(body: TokenizationRecord):
    return _fingerprint(body)


@router.post("/validate-token")
def validate_token(body: TokenRecord):
    return _fingerprint(body)


@router.post("/validate-morpheme")
def validate_morpheme(body: MorphemeRecord):
    return _fingerprint(body)


@router.post("/validate-morphology")
def validate_morphology(body: MorphologicalAnnotation):
    return _fingerprint(body)


@router.post("/validate-pos")
def validate_pos(body: PartOfSpeechAnnotation):
    return _fingerprint(body)


@router.post("/validate-dependency-parse")
def validate_dependency_parse(body: DependencyParseRecord):
    return _fingerprint(body)


@router.post("/validate-dependency-relation")
def validate_dependency_relation(body: DependencyRelation):
    return _fingerprint(body)


@router.post("/validate-constituency-parse")
def validate_constituency_parse(body: ConstituencyParseRecord):
    return _fingerprint(body)


@router.post("/validate-constituency-node")
def validate_constituency_node(body: ConstituencyNode):
    return _fingerprint(body)


@router.post("/validate-bundle")
def validate_bundle(body: LinguisticAnnotationBundle):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "bundle_fingerprint_sha256": body.fingerprint(),
    }
