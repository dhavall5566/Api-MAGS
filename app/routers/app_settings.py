from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.db_helpers import get_config, upsert_config

router = APIRouter(prefix="/api/app-settings", tags=["app-settings"])

CONFIG_KEY = "client_app_state"

DEFAULT_STATE = {
    "navOrder": None,
    "hiddenNavHrefs": [],
    "rolePermissions": None,
    "userPermissionOverrides": {},
    "settings": None,
    "reports": [],
}


@router.get("")
def get_app_settings(db: Session = Depends(get_db)):
    stored = get_config(db, CONFIG_KEY, {})
    return {**DEFAULT_STATE, **(stored if isinstance(stored, dict) else {})}


@router.put("")
def put_app_settings(body: dict, db: Session = Depends(get_db)):
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Expected JSON object")
    current = get_config(db, CONFIG_KEY, {})
    if not isinstance(current, dict):
        current = {}
    merged = {**DEFAULT_STATE, **current, **body}
    upsert_config(db, CONFIG_KEY, merged)
    db.commit()
    return merged
