from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from ..dependencies import get_session, require_read, require_write
from ..schemas import PredicateCreate, PredicateList, PredicateRead, PredicateUpdate
from ..services.predicates import create_predicate, get_predicate_or_404, list_predicates, update_predicate

router = APIRouter(prefix="/v1/predicates", tags=["Predicate Registry"])

@router.get("", response_model=PredicateList, dependencies=[Depends(require_read)])
def get_predicates(status_value: str | None = Query(default=None, alias="status"), visibility: str | None = None, db: Session = Depends(get_session)):
    items, total = list_predicates(db, status_value=status_value, visibility=visibility)
    return PredicateList(items=items, total=total)

@router.post("", response_model=PredicateRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_write)])
def post_predicate(payload: PredicateCreate, db: Session = Depends(get_session)):
    return create_predicate(db, payload)

@router.get("/{predicate_id}", response_model=PredicateRead, dependencies=[Depends(require_read)])
def get_predicate(predicate_id: str, db: Session = Depends(get_session)):
    return get_predicate_or_404(db, predicate_id)

@router.patch("/{predicate_id}", response_model=PredicateRead, dependencies=[Depends(require_write)])
def patch_predicate(predicate_id: str, payload: PredicateUpdate, db: Session = Depends(get_session)):
    return update_predicate(db, predicate_id, payload)
