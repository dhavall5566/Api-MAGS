from sqlalchemy.orm import Session

from app.models import (
    AppConfig,
    Challan,
    Consumption,
    PowderCoating,
    Profile,
    PurchaseOrder,
    Scrap,
    SeriesName,
    StockInward,
    StockLedgerEntry,
    User,
    Vendor,
)


def rows_as_dicts(rows) -> list[dict]:
    return [row.data for row in rows]


def normalize_profile_data(data: dict) -> dict:
    """Normalize profile JSON: dyeCode migration and strip removed fields."""
    dye_code = str(data.get("dyeCode") or data.get("diaCode") or "").strip()
    normalized = dict(data)
    for key in ("lengthsInMeter", "rate", "perKgRate", "priceHistory"):
        normalized.pop(key, None)
    if dye_code:
        normalized["dyeCode"] = dye_code
    return normalized


def profile_rows_as_dicts(rows) -> list[dict]:
    return [normalize_profile_data(row.data) for row in rows]


def normalize_purchase_order_data(data: dict) -> dict:
    """Strip legacy vehicleNumber from purchase order JSON."""
    normalized = dict(data)
    normalized.pop("vehicleNumber", None)
    return normalized


def purchase_order_rows_as_dicts(rows) -> list[dict]:
    return [normalize_purchase_order_data(row.data) for row in rows]


def upsert_entity(db: Session, model, item: dict) -> dict:
    entity_id = item.get("id")
    if not entity_id:
        raise ValueError("Entity id is required")
    row = db.get(model, entity_id)
    if row:
        row.data = item
    else:
        row = model(id=entity_id, data=item)
        db.add(row)
    db.commit()
    db.refresh(row)
    return item


def delete_entity(db: Session, model, entity_id: str) -> bool:
    row = db.get(model, entity_id)
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True


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
        PurchaseOrder,
        AppConfig,
    ):
        db.query(model).delete()
    db.commit()
