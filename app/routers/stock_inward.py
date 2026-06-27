from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import StockInward
from app.services.db_helpers import (
    delete_entity,
    normalize_stock_inward_data,
    split_stock_inward_entry,
    stock_inward_rows_as_dicts,
    upsert_entity,
)

router = APIRouter(prefix="/api/stock-inward", tags=["stock-inward"])


@router.get("")
def list_stock_inward(db: Session = Depends(get_db)):
    rows = db.query(StockInward).all()
    return {"stockInward": stock_inward_rows_as_dicts(rows)}


@router.post("")
def create_stock_inward(body: dict, db: Session = Depends(get_db)):
    if not body.get("id"):
        raise HTTPException(status_code=400, detail="id is required")
    saved = upsert_entity(db, StockInward, normalize_stock_inward_data(body))
    return {"stockInward": saved}


@router.put("/{entry_id}")
def update_stock_inward(entry_id: str, body: dict, db: Session = Depends(get_db)):
    if body.get("id") and body["id"] != entry_id:
        raise HTTPException(status_code=400, detail="id mismatch")
    body["id"] = entry_id
    row = db.get(StockInward, entry_id)
    if not row:
        raise HTTPException(status_code=404, detail="Stock inward entry not found")
    saved = upsert_entity(db, StockInward, normalize_stock_inward_data(body))
    return {"stockInward": saved}


@router.delete("/{entry_id}")
def remove_stock_inward(entry_id: str, db: Session = Depends(get_db)):
    if not delete_entity(db, StockInward, entry_id):
        raise HTTPException(status_code=404, detail="Stock inward entry not found")
    return {"ok": True, "id": entry_id}


@router.post("/{entry_id}/split")
def split_stock_inward(entry_id: str, body: dict, db: Session = Depends(get_db)):
    raw_pieces = body.get("pieces") or []
    if not isinstance(raw_pieces, list):
        raise HTTPException(status_code=400, detail="pieces must be an array")

    pieces = [{"length": piece.get("length")} for piece in raw_pieces if isinstance(piece, dict)]
    try:
        result = split_stock_inward_entry(db, entry_id, pieces)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return result
