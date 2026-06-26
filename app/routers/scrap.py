from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Scrap
from app.services.db_helpers import rows_as_dicts

router = APIRouter(prefix="/api/scrap", tags=["scrap"])


@router.get("")
def list_scrap(db: Session = Depends(get_db)):
    rows = db.query(Scrap).all()
    return {"scrap": rows_as_dicts(rows)}
