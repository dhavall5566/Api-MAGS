from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import SeriesName
from app.services.db_helpers import rows_as_dicts

router = APIRouter(prefix="/api/series", tags=["series"])


@router.get("")
def list_series(db: Session = Depends(get_db)):
    rows = db.query(SeriesName).all()
    return {"series": rows_as_dicts(rows)}
