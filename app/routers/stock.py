from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import StockInward, StockLedgerEntry
from app.services.db_helpers import rows_as_dicts, stock_inward_rows_as_dicts

router = APIRouter(prefix="/api/stock", tags=["stock"])


@router.get("")
def list_stock(db: Session = Depends(get_db)):
    inward = db.query(StockInward).all()
    ledger = db.query(StockLedgerEntry).all()
    return {
        "inward": stock_inward_rows_as_dicts(inward),
        "ledger": rows_as_dicts(ledger),
    }
