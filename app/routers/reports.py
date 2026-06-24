from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.db_helpers import get_config

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("")
def get_reports(db: Session = Depends(get_db)):
    return {
        "monthlyStockMovement": get_config(db, "monthlyStockMovement", []),
        "consumptionTrends": get_config(db, "consumptionTrends", []),
        "colorDistribution": get_config(db, "colorDistribution", []),
        "inventoryByCategory": get_config(db, "inventoryByCategory", []),
        "summary": get_config(db, "reportSummary", {}),
    }
