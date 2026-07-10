from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session
from ..dependencies import get_session, require_read, require_write
from ..schemas import GraphEdge, GraphNode, GraphPath, GraphPathResult, GraphTraversal, NeighborhoodGroup, NeighborhoodResult, Recommendation, RecommendationResult, RelationshipCreate, RelationshipList, RelationshipRead, RelationshipReviewCreate, RelationshipReviewRead
from ..services.relationships import create_relationship, find_paths, list_relationships, list_reviews, neighborhood, recommendations, review_relationship, traverse_graph

router = APIRouter(prefix="/v1", tags=["Relationships and Graph"])

@router.get("/relationships", response_model=RelationshipList, dependencies=[Depends(require_read)])
def get_relationships(request: Request, subject_id: str | None = None, object_id: str | None = None, predicate: str | None = None, status_value: str | None = Query(default=None, alias="status"), min_confidence: float | None = Query(default=None, ge=0.0, le=1.0), limit: int = Query(default=50, ge=1), offset: int = Query(default=0, ge=0), db: Session = Depends(get_session)):
    limit = min(limit, request.app.state.settings.page_size_max)
    items, total = list_relationships(db, subject_id=subject_id, object_id=object_id, predicate=predicate, status_value=status_value, min_confidence=min_confidence, limit=limit, offset=offset)
    return RelationshipList(items=items, total=total, limit=limit, offset=offset)

@router.post("/relationships", response_model=RelationshipRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_write)])
def post_relationship(payload: RelationshipCreate, db: Session = Depends(get_session)):
    return create_relationship(db, payload)

@router.post("/relationships/bulk", response_model=list[RelationshipRead], dependencies=[Depends(require_write)])
def post_relationships_bulk(payloads: list[RelationshipCreate], db: Session = Depends(get_session)):
    if len(payloads) > 1000:
        from fastapi import HTTPException
        raise HTTPException(status_code=413, detail="Bulk limit is 1000 relationships.")
    return [create_relationship(db, payload) for payload in payloads]

@router.post("/relationships/{relationship_id}/reviews", response_model=RelationshipReviewRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_write)])
def post_relationship_review(relationship_id: str, payload: RelationshipReviewCreate, db: Session = Depends(get_session)):
    return review_relationship(db, relationship_id=relationship_id, payload=payload)

@router.get("/relationship-reviews", response_model=list[RelationshipReviewRead], dependencies=[Depends(require_read)])
def get_relationship_reviews(relationship_id: str | None = None, decision: str | None = None, limit: int = Query(default=50, ge=1, le=200), db: Session = Depends(get_session)):
    return list_reviews(db, relationship_id=relationship_id, decision=decision, limit=limit)

@router.get("/graph/path", response_model=GraphPathResult, dependencies=[Depends(require_read)])
def get_graph_path(request: Request, source_id: str, target_id: str, direction: str = Query(default="both", pattern="^(outbound|inbound|both)$"), depth: int = Query(default=4, ge=1), max_paths: int = Query(default=5, ge=1, le=20), predicates: list[str] | None = Query(default=None), statuses: list[str] | None = Query(default=["verified", "approved"]), min_confidence: float = Query(default=0.0, ge=0.0, le=1.0), db: Session = Depends(get_session)):
    depth = min(depth, request.app.state.settings.max_graph_depth)
    paths = find_paths(db, source_id=source_id, target_id=target_id, direction=direction, max_depth=depth, max_paths=max_paths, predicates=predicates, statuses=statuses, min_confidence=min_confidence)
    return GraphPathResult(source_id=source_id, target_id=target_id, direction=direction, max_depth=depth, paths=[GraphPath(node_ids=n, relationships=r, length=len(r), score=s) for n, r, s in paths])

@router.get("/graph/{entity_id:path}/neighborhood", response_model=NeighborhoodResult, dependencies=[Depends(require_read)])
def get_neighborhood(entity_id: str, statuses: list[str] | None = Query(default=["verified", "approved"]), min_confidence: float = Query(default=0.0, ge=0.0, le=1.0), db: Session = Depends(get_session)):
    root, groups, total = neighborhood(db, root_id=entity_id, statuses=statuses, min_confidence=min_confidence)
    return NeighborhoodResult(root=root, groups=[NeighborhoodGroup(**group) for group in groups], total_relationships=total)

@router.get("/graph/{entity_id:path}/recommendations", response_model=RecommendationResult, dependencies=[Depends(require_read)])
def get_recommendations(entity_id: str, target_type: str | None = None, limit: int = Query(default=10, ge=1, le=50), statuses: list[str] | None = Query(default=["verified", "approved"]), min_confidence: float = Query(default=0.0, ge=0.0, le=1.0), db: Session = Depends(get_session)):
    items = recommendations(db, root_id=entity_id, target_type=target_type, limit=limit, statuses=statuses, min_confidence=min_confidence)
    return RecommendationResult(root_id=entity_id, items=[Recommendation(**item) for item in items])

@router.get("/graph/{entity_id:path}", response_model=GraphTraversal, dependencies=[Depends(require_read)])
def get_graph(request: Request, entity_id: str, direction: str = Query(default="both", pattern="^(outbound|inbound|both)$"), depth: int = Query(default=1, ge=1), predicates: list[str] | None = Query(default=None), statuses: list[str] | None = Query(default=None), min_confidence: float = Query(default=0.0, ge=0.0, le=1.0), db: Session = Depends(get_session)):
    depth = min(depth, request.app.state.settings.max_graph_depth)
    nodes, edges = traverse_graph(db, root_id=entity_id, direction=direction, max_depth=depth, predicates=predicates, statuses=statuses, min_confidence=min_confidence)
    return GraphTraversal(root_id=entity_id, direction=direction, max_depth=depth, nodes=[GraphNode(entity=e, depth=d) for e, d in nodes], edges=[GraphEdge(relationship=r, depth=d) for r, d in edges])
