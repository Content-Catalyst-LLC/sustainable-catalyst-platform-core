from fastapi import APIRouter
from app.services.semantic_synthesis_research_answer import (
    ResearchAnswerObject, SemanticSynthesisResearchAnswerBundle, SynthesisClaim,
    contract_document, reference_semantic_synthesis_research_answer_bundle,
)
router=APIRouter(prefix="/v1/research-answers",tags=["semantic-synthesis-research-answer"])
public_router=APIRouter(prefix="/public/v1/research-answers",tags=["semantic-synthesis-research-answer-public"])
@public_router.get("/contract")
def public_contract(): return contract_document()
@router.get("/contract")
def contract(): return contract_document()
@router.get("/reference")
def reference():
    b=reference_semantic_synthesis_research_answer_bundle(); return {"ok":True,"bundle_fingerprint_sha256":b.fingerprint(),"bundle":b.model_dump(mode="json")}
@router.get("/reference/answers")
def reference_answers():
    xs=reference_semantic_synthesis_research_answer_bundle().research_answers; return {"ok":True,"count":len(xs),"items":[x.model_dump(mode="json") for x in xs]}
@router.get("/reference/synthesis-claims")
def reference_synthesis_claims():
    xs=reference_semantic_synthesis_research_answer_bundle().synthesis_claims; return {"ok":True,"count":len(xs),"items":[x.model_dump(mode="json") for x in xs]}
@router.post("/validate-answer")
def validate_answer(payload:ResearchAnswerObject): return {"ok":True,"fingerprint_sha256":payload.fingerprint()}
@router.post("/validate-synthesis-claim")
def validate_synthesis_claim(payload:SynthesisClaim): return {"ok":True,"fingerprint_sha256":payload.fingerprint()}
@router.post("/validate-bundle")
def validate_bundle(payload:SemanticSynthesisResearchAnswerBundle): return {"ok":True,"fingerprint_sha256":payload.fingerprint()}
