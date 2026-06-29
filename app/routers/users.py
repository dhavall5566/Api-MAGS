from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.services.db_helpers import delete_entity, rows_as_dicts, upsert_entity

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("")
def list_users(db: Session = Depends(get_db)):
    rows = db.query(User).all()
    return {"users": rows_as_dicts(rows)}


@router.post("")
def create_user(body: dict, db: Session = Depends(get_db)):
    if not body.get("id"):
        raise HTTPException(status_code=400, detail="id is required")
    saved = upsert_entity(db, User, body)
    return {"user": saved}


@router.put("/{user_id}")
def update_user(user_id: str, body: dict, db: Session = Depends(get_db)):
    if body.get("id") and body["id"] != user_id:
        raise HTTPException(status_code=400, detail="id mismatch")
    body["id"] = user_id
    row = db.get(User, user_id)
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    merged = {**row.data, **body, "id": user_id}
    saved = upsert_entity(db, User, merged)
    return {"user": saved}


@router.delete("/{user_id}")
def remove_user(user_id: str, db: Session = Depends(get_db)):
    if not delete_entity(db, User, user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return {"ok": True, "id": user_id}
