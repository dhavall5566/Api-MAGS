from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Profile
from app.services.db_helpers import rows_as_dicts

router = APIRouter(prefix="/api/profiles", tags=["profiles"])


@router.get("")
def list_profiles(db: Session = Depends(get_db)):
    rows = db.query(Profile).all()
    return {"profiles": rows_as_dicts(rows)}
