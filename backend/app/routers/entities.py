from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from ..dependencies import get_session, require_read, require_write
from ..schemas import (
    AliasCreate,
    AliasRead,
    EntityCreate,
    EntityList,
    EntityRead,
    EntityUpdate,
)
from ..services.entities import (
    add_alias,
    create_entity,
    get_entity_or_404,
    list_entities,
    resolve_alias,
    update_entity,
)

router = APIRouter(prefix="/v1/entities", tags=["Entities"])


@router.get("", response_model=EntityList, dependencies=[Depends(require_read)])
def get_entities(
    request: Request,
    q: str | None = None,
    entity_type: str | None = None,
    status_value: str | None = Query(default=None, alias="status"),
    visibility: str | None = None,
    limit: int = Query(default=50, ge=1),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_session),
):
    max_limit = request.app.state.settings.page_size_max
    limit = min(limit, max_limit)
    items, total = list_entities(
        db,
        query=q,
        entity_type=entity_type,
        status_value=status_value,
        visibility=visibility,
        limit=limit,
        offset=offset,
    )
    return EntityList(items=items, total=total, limit=limit, offset=offset)


@router.post(
    "",
    response_model=EntityRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_write)],
)
def post_entity(
    payload: EntityCreate,
    db: Session = Depends(get_session),
):
    return create_entity(db, payload)


@router.post(
    "/bulk",
    response_model=list[EntityRead],
    dependencies=[Depends(require_write)],
)
def post_entities_bulk(
    payloads: list[EntityCreate],
    db: Session = Depends(get_session),
):
    if len(payloads) > 500:
        from fastapi import HTTPException
        raise HTTPException(status_code=413, detail="Bulk limit is 500 entities.")
    return [create_entity(db, payload) for payload in payloads]


@router.get(
    "/resolve",
    response_model=EntityRead,
    dependencies=[Depends(require_read)],
)
def get_entity_by_alias(
    namespace: str,
    value: str,
    db: Session = Depends(get_session),
):
    return resolve_alias(db, namespace, value)


@router.get(
    "/{entity_id:path}",
    response_model=EntityRead,
    dependencies=[Depends(require_read)],
)
def get_entity(
    entity_id: str,
    db: Session = Depends(get_session),
):
    return get_entity_or_404(db, entity_id)


@router.patch(
    "/{entity_id:path}",
    response_model=EntityRead,
    dependencies=[Depends(require_write)],
)
def patch_entity(
    entity_id: str,
    payload: EntityUpdate,
    db: Session = Depends(get_session),
):
    return update_entity(db, entity_id, payload)


@router.post(
    "/{entity_id:path}/aliases",
    response_model=AliasRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_write)],
)
def post_alias(
    entity_id: str,
    payload: AliasCreate,
    db: Session = Depends(get_session),
):
    return add_alias(db, entity_id, payload)
