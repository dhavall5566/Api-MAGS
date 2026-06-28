from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Profile
from app.services.db_helpers import (
    delete_entity,
    normalize_profile_data,
    profile_rows_as_dicts,
    upsert_entity,
)

router = APIRouter(prefix="/api/profiles", tags=["profiles"])


@router.get("")
def list_profiles(db: Session = Depends(get_db)):
    rows = db.query(Profile).all()
    return {"profiles": profile_rows_as_dicts(rows)}


@router.post("")
def create_profile(body: dict, db: Session = Depends(get_db)):
    if not body.get("id"):
        raise HTTPException(status_code=400, detail="id is required")
    saved = upsert_entity(db, Profile, normalize_profile_data(body))
    return {"profile": normalize_profile_data(saved)}


@router.put("/{profile_id}")
def update_profile(profile_id: str, body: dict, db: Session = Depends(get_db)):
    if body.get("id") and body["id"] != profile_id:
        raise HTTPException(status_code=400, detail="id mismatch")
    body["id"] = profile_id
    row = db.get(Profile, profile_id)
    if not row:
        raise HTTPException(status_code=404, detail="Profile not found")
    merged = {**row.data, **body, "id": profile_id}
    saved = upsert_entity(db, Profile, normalize_profile_data(merged))
    return {"profile": normalize_profile_data(saved)}


@router.delete("/{profile_id}")
def remove_profile(profile_id: str, db: Session = Depends(get_db)):
    if not delete_entity(db, Profile, profile_id):
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"ok": True, "id": profile_id}
