from sqlalchemy.orm import Session

from app.models import (
    AppConfig,
    Challan,
    Consumption,
    PowderCoating,
    Profile,
    Scrap,
    SeriesName,
    StockInward,
    StockLedgerEntry,
    User,
    Vendor,
)


def rows_as_dicts(rows) -> list[dict]:
    return [row.data for row in rows]


def get_config(db: Session, key: str, default=None):
    row = db.get(AppConfig, key)
    return row.data if row else default


def upsert_config(db: Session, key: str, data) -> None:
    row = db.get(AppConfig, key)
    if row:
        row.data = data
    else:
        db.add(AppConfig(key=key, data=data))


def clear_all_data(db: Session) -> None:
    for model in (
        Profile,
        User,
        Vendor,
        SeriesName,
        StockInward,
        StockLedgerEntry,
        Consumption,
        PowderCoating,
        Scrap,
        Challan,
        AppConfig,
    ):
        db.query(model).delete()
    db.commit()
