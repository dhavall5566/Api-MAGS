from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import PowderCoating
from app.services.db_helpers import delete_entity, rows_as_dicts, upsert_entity

router = APIRouter(prefix="/api/powder-coating", tags=["powder-coating"])


@router.get("")
def list_powder_coating(db: Session = Depends(get_db)):
    rows = db.query(PowderCoating).all()
    return {"powderCoating": rows_as_dicts(rows)}


@router.post("")
def create_powder_coating(body: dict, db: Session = Depends(get_db)):
    if not body.get("id"):
        raise HTTPException(status_code=400, detail="id is required")
    saved = upsert_entity(db, PowderCoating, body)
    return {"powderCoating": saved}


@router.put("/{entry_id}")
def update_powder_coating(entry_id: str, body: dict, db: Session = Depends(get_db)):
    if body.get("id") and body["id"] != entry_id:
        raise HTTPException(status_code=400, detail="id mismatch")
    body["id"] = entry_id
    row = db.get(PowderCoating, entry_id)
    if not row:
        raise HTTPException(status_code=404, detail="Powder coating entry not found")
    merged = {**row.data, **body, "id": entry_id}
    saved = upsert_entity(db, PowderCoating, merged)
    return {"powderCoating": saved}


@router.delete("/{entry_id}")
def remove_powder_coating(entry_id: str, db: Session = Depends(get_db)):
    if not delete_entity(db, PowderCoating, entry_id):
        raise HTTPException(status_code=404, detail="Powder coating entry not found")
    return {"ok": True, "id": entry_id}
