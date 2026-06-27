from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Challan
from app.services.db_helpers import (
    challan_rows_as_dicts,
    delete_entity,
    normalize_challan_data,
    upsert_entity,
)

router = APIRouter(prefix="/api/challans", tags=["challans"])


@router.get("")
def list_challans(db: Session = Depends(get_db)):
    rows = db.query(Challan).all()
    return {"challans": challan_rows_as_dicts(rows)}


@router.post("")
def create_challan(body: dict, db: Session = Depends(get_db)):
    if not body.get("id"):
        raise HTTPException(status_code=400, detail="id is required")
    saved = upsert_entity(db, Challan, normalize_challan_data(body))
    return {"challan": normalize_challan_data(saved)}


@router.put("/{challan_id}")
def update_challan(challan_id: str, body: dict, db: Session = Depends(get_db)):
    if body.get("id") and body["id"] != challan_id:
        raise HTTPException(status_code=400, detail="id mismatch")
    body["id"] = challan_id
    row = db.get(Challan, challan_id)
    if not row:
        raise HTTPException(status_code=404, detail="Challan not found")
    saved = upsert_entity(db, Challan, normalize_challan_data(body))
    return {"challan": normalize_challan_data(saved)}


@router.delete("/{challan_id}")
def remove_challan(challan_id: str, db: Session = Depends(get_db)):
    if not delete_entity(db, Challan, challan_id):
        raise HTTPException(status_code=404, detail="Challan not found")
    return {"ok": True, "id": challan_id}
