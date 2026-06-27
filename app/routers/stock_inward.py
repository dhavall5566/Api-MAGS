from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import StockInward
from app.services.db_helpers import (
    delete_entity,
    normalize_stock_inward_data,
    split_stock_inward_entry,
    stock_inward_rows_as_dicts,
    upsert_entities,
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


@router.post("/batch")
def create_stock_inward_batch(body: dict, db: Session = Depends(get_db)):
    raw_entries = body.get("entries")
    if not isinstance(raw_entries, list) or not raw_entries:
        raise HTTPException(status_code=400, detail="entries array is required")

    normalized_items: list[dict] = []
    for entry in raw_entries:
        if not isinstance(entry, dict) or not entry.get("id"):
            raise HTTPException(status_code=400, detail="each entry requires an id")
        normalized_items.append(normalize_stock_inward_data(entry))

    try:
        saved = upsert_entities(db, StockInward, normalized_items)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

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
