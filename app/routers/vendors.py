from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Vendor
from app.services.db_helpers import (
    delete_entity,
    format_vendor_delete_block_message,
    get_vendor_delete_associations,
    merge_canonical_vendors,
    normalize_vendor_data,
    upsert_entity,
    vendor_rows_as_dicts,
)

router = APIRouter(prefix="/api/vendors", tags=["vendors"])


@router.get("")
def list_vendors(db: Session = Depends(get_db)):
    rows = db.query(Vendor).all()
    return {"vendors": merge_canonical_vendors(vendor_rows_as_dicts(rows))}


@router.post("")
def create_vendor(body: dict, db: Session = Depends(get_db)):
    if not body.get("id"):
        raise HTTPException(status_code=400, detail="id is required")
    saved = upsert_entity(db, Vendor, normalize_vendor_data(body))
    return {"vendor": normalize_vendor_data(saved)}


@router.put("/{vendor_id}")
def update_vendor(vendor_id: str, body: dict, db: Session = Depends(get_db)):
    if body.get("id") and body["id"] != vendor_id:
        raise HTTPException(status_code=400, detail="id mismatch")
    body["id"] = vendor_id
    row = db.get(Vendor, vendor_id)
    if not row:
        raise HTTPException(status_code=404, detail="Vendor not found")
    merged = {**row.data, **body, "id": vendor_id}
    saved = upsert_entity(db, Vendor, normalize_vendor_data(merged))
    return {"vendor": normalize_vendor_data(saved)}


@router.delete("/{vendor_id}")
def remove_vendor(vendor_id: str, db: Session = Depends(get_db)):
    row = db.get(Vendor, vendor_id)
    if not row:
        raise HTTPException(status_code=404, detail="Vendor not found")

    vendor = normalize_vendor_data(row.data)
    associations = get_vendor_delete_associations(db, vendor)
    if associations:
        vendor_name = str(vendor.get("partyName") or vendor_id).strip()
        raise HTTPException(
            status_code=409,
            detail=format_vendor_delete_block_message(vendor_name, associations),
        )

    if not delete_entity(db, Vendor, vendor_id):
        raise HTTPException(status_code=404, detail="Vendor not found")
    return {"ok": True, "id": vendor_id}
