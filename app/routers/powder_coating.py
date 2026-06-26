from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import PowderCoating
from app.services.db_helpers import rows_as_dicts

router = APIRouter(prefix="/api/powder-coating", tags=["powder-coating"])


@router.get("")
def list_powder_coating(db: Session = Depends(get_db)):
    rows = db.query(PowderCoating).all()
    return {"powderCoating": rows_as_dicts(rows)}
