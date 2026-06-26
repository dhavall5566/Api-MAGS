"""Migrate purchase order JSONB: remove vehicleNumber, ensure new contact fields."""

from app.database import SessionLocal
from app.models import PurchaseOrder


def normalize_purchase_order_data(data: dict) -> dict:
    normalized = dict(data)
    normalized.pop("vehicleNumber", None)
    for key in ("gstNo", "personName", "contactNo"):
        normalized.setdefault(key, normalized.get(key) or "")
    return normalized


def migrate() -> int:
    db = SessionLocal()
    updated = 0
    try:
        rows = db.query(PurchaseOrder).all()
        for row in rows:
            normalized = normalize_purchase_order_data(dict(row.data))
            if normalized != row.data:
                row.data = normalized
                updated += 1
        db.commit()
    finally:
        db.close()
    return updated


if __name__ == "__main__":
    count = migrate()
    print(f"Migrated {count} purchase order(s).")
