from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.dashboard import VALID_TIMEFRAMES, build_dashboard_payload
from app.services.db_helpers import get_config

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

DEFAULT_TIMEFRAME = "financial-year"


@router.get("")
def get_dashboard(
    range: str = Query(DEFAULT_TIMEFRAME, alias="range"),
    db: Session = Depends(get_db),
):
    timeframe = range if range in VALID_TIMEFRAMES else DEFAULT_TIMEFRAME
    config = {
        "dashboard_stats": get_config(db, "dashboard_stats", {}),
        "dashboard_charts": get_config(db, "dashboard_charts", {}),
        "notifications": get_config(db, "notifications", []),
        "recent_transactions": get_config(db, "recent_transactions", []),
    }
    return build_dashboard_payload(timeframe, config)
