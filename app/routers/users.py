from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.services.db_helpers import rows_as_dicts

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("")
def list_users(db: Session = Depends(get_db)):
    rows = db.query(User).all()
    return {"users": rows_as_dicts(rows)}
