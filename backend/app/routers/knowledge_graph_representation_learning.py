from fastapi import APIRouter
from app.services.knowledge_graph_representation_learning import *

router = APIRouter(prefix="/v1/kg-representation", tags=["knowledge-graph-representation-learning"])
public_router = APIRouter(prefix="/public/v1/kg-representation", tags=["public-knowledge-graph-representation-learning"])

@router.get("/contract")
def get_contract(): return contract_document()
@public_router.get("/contract")
def get_public_contract(): return contract_document()
@router.get("/reference")
def get_reference():
    b=reference_knowledge_graph_representation_learning_bundle(); return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"bundle":b.model_dump(mode="json",exclude_none=True),"bundle_fingerprint_sha256":b.fingerprint()}
@router.post("/validate-runtime")
def validate_runtime(body:KnowledgeGraphRepresentationRuntimeContract): return {"ok":True,"fingerprint_sha256":body.fingerprint()}
@router.post("/validate-vector")
def validate_vector(body:KGRepresentationVector): return {"ok":True,"fingerprint_sha256":body.fingerprint()}
@router.post("/validate-triple-score")
def validate_triple_score(body:KGTripleScoreRecord): return {"ok":True,"fingerprint_sha256":body.fingerprint()}
@router.post("/validate-bundle")
def validate_bundle(body:KnowledgeGraphRepresentationLearningBundle): return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"bundle_fingerprint_sha256":body.fingerprint()}
