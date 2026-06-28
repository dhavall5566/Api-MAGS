from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import SeriesName
from app.services.db_helpers import (
    count_profiles_for_series_label,
    delete_entity,
    enrich_series_dict,
    get_series_label,
    normalize_series_data,
    series_rows_as_dicts,
    upsert_entity,
)

router = APIRouter(prefix="/api/series", tags=["series"])


@router.get("")
def list_series(db: Session = Depends(get_db)):
    rows = db.query(SeriesName).all()
    return {"series": series_rows_as_dicts(db, rows)}


@router.post("")
def create_series(body: dict, db: Session = Depends(get_db)):
    if not body.get("id"):
        raise HTTPException(status_code=400, detail="id is required")
    saved = upsert_entity(db, SeriesName, normalize_series_data(body))
    return {"series": enrich_series_dict(db, saved)}


@router.put("/{series_id}")
def update_series(series_id: str, body: dict, db: Session = Depends(get_db)):
    if body.get("id") and body["id"] != series_id:
        raise HTTPException(status_code=400, detail="id mismatch")
    body["id"] = series_id
    row = db.get(SeriesName, series_id)
    if not row:
        raise HTTPException(status_code=404, detail="Series not found")
    merged = {**row.data, **body, "id": series_id}
    saved = upsert_entity(db, SeriesName, normalize_series_data(merged))
    return {"series": enrich_series_dict(db, saved)}


@router.delete("/{series_id}")
def remove_series(series_id: str, db: Session = Depends(get_db)):
    row = db.get(SeriesName, series_id)
    if not row:
        raise HTTPException(status_code=404, detail="Series not found")

    label = get_series_label(row.data)
    profile_count = count_profiles_for_series_label(db, label)
    if profile_count > 0:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Cannot delete this series because {profile_count} profile(s) "
                "in Profile Master are linked to it."
            ),
        )

    if not delete_entity(db, SeriesName, series_id):
        raise HTTPException(status_code=404, detail="Series not found")
    return {"ok": True, "id": series_id}
