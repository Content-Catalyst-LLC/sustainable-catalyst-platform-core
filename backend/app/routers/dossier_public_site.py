from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..dependencies import get_session
from ..models import SignatureDossier
from ..services.workflows import dossier_read, get_dossier_or_404, verify_dossier

router = APIRouter(prefix="/public/dossiers", tags=["Public Dossier Records"])


@router.get("")
def list_public_dossiers(db: Session = Depends(get_session)):
    records = list(db.scalars(select(SignatureDossier).where(SignatureDossier.visibility == "public", SignatureDossier.status.in_(["finalized", "superseded"])).order_by(SignatureDossier.signed_at.desc())).all())
    return {"items": [dossier_read(db, item, include_private_records=False).model_dump(mode="json") for item in records], "total": len(records)}


@router.get("/{dossier_id:path}/verify")
def verify_public_dossier(request: Request, dossier_id: str, db: Session = Depends(get_session)):
    dossier = get_dossier_or_404(db, dossier_id)
    if dossier.visibility != "public" or dossier.status not in {"finalized", "superseded"}:
        raise HTTPException(status_code=404, detail="Dossier not found.")
    return verify_dossier(db, dossier_id, request.app.state.settings)


@router.get("/{dossier_id:path}")
def get_public_dossier(dossier_id: str, db: Session = Depends(get_session)):
    dossier = get_dossier_or_404(db, dossier_id)
    if dossier.visibility != "public" or dossier.status not in {"finalized", "superseded"}:
        raise HTTPException(status_code=404, detail="Dossier not found.")
    return dossier_read(db, dossier, include_private_records=False)
