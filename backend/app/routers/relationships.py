from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from ..dependencies import get_session, require_read, require_write
from ..schemas import (
    GraphEdge,
    GraphNode,
    GraphTraversal,
    RelationshipCreate,
    RelationshipList,
    RelationshipRead,
)
from ..services.relationships import (
    create_relationship,
    list_relationships,
    traverse_graph,
)

router = APIRouter(prefix="/v1", tags=["Relationships and Graph"])


@router.get(
    "/relationships",
    response_model=RelationshipList,
    dependencies=[Depends(require_read)],
)
def get_relationships(
    request: Request,
    subject_id: str | None = None,
    object_id: str | None = None,
    predicate: str | None = None,
    status_value: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_session),
):
    limit = min(limit, request.app.state.settings.page_size_max)
    items, total = list_relationships(
        db,
        subject_id=subject_id,
        object_id=object_id,
        predicate=predicate,
        status_value=status_value,
        limit=limit,
        offset=offset,
    )
    return RelationshipList(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/relationships",
    response_model=RelationshipRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_write)],
)
def post_relationship(
    payload: RelationshipCreate,
    db: Session = Depends(get_session),
):
    return create_relationship(db, payload)


@router.post(
    "/relationships/bulk",
    response_model=list[RelationshipRead],
    dependencies=[Depends(require_write)],
)
def post_relationships_bulk(
    payloads: list[RelationshipCreate],
    db: Session = Depends(get_session),
):
    if len(payloads) > 1000:
        from fastapi import HTTPException
        raise HTTPException(status_code=413, detail="Bulk limit is 1000 relationships.")
    return [create_relationship(db, payload) for payload in payloads]


@router.get(
    "/graph/{entity_id:path}",
    response_model=GraphTraversal,
    dependencies=[Depends(require_read)],
)
def get_graph(
    request: Request,
    entity_id: str,
    direction: str = Query(default="both", pattern="^(outbound|inbound|both)$"),
    depth: int = Query(default=1, ge=1),
    predicates: list[str] | None = Query(default=None),
    db: Session = Depends(get_session),
):
    max_allowed = request.app.state.settings.max_graph_depth
    depth = min(depth, max_allowed)
    nodes, edges = traverse_graph(
        db,
        root_id=entity_id,
        direction=direction,
        max_depth=depth,
        predicates=predicates,
    )
    return GraphTraversal(
        root_id=entity_id,
        direction=direction,
        max_depth=depth,
        nodes=[GraphNode(entity=entity, depth=d) for entity, d in nodes],
        edges=[
            GraphEdge(relationship=relationship, depth=d)
            for relationship, d in edges
        ],
    )
