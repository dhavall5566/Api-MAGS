from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Vendor
from app.services.db_helpers import vendor_rows_as_dicts

router = APIRouter(prefix="/api/vendors", tags=["vendors"])


@router.get("")
def list_vendors(db: Session = Depends(get_db)):
    rows = db.query(Vendor).all()
    return {"vendors": vendor_rows_as_dicts(rows)}
