from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Consumption
from app.services.db_helpers import rows_as_dicts

router = APIRouter(prefix="/api/consumption", tags=["consumption"])


@router.get("")
def list_consumption(db: Session = Depends(get_db)):
    rows = db.query(Consumption).all()
    return {"consumption": rows_as_dicts(rows)}
