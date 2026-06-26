from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Challan
from app.services.db_helpers import rows_as_dicts

router = APIRouter(prefix="/api/challans", tags=["challans"])


@router.get("")
def list_challans(db: Session = Depends(get_db)):
    rows = db.query(Challan).all()
    return {"challans": rows_as_dicts(rows)}
