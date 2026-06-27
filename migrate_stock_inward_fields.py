"""Migrate stock inward JSONB: remove lengthFeet/rate, ensure new fields."""

from app.database import SessionLocal
from app.models import StockInward
from app.services.db_helpers import normalize_stock_inward_data


def migrate() -> int:
    db = SessionLocal()
    updated = 0
    try:
        rows = db.query(StockInward).all()
        for row in rows:
            normalized = normalize_stock_inward_data(dict(row.data))
            if normalized != row.data:
                row.data = normalized
                updated += 1
        db.commit()
    finally:
        db.close()
    return updated


if __name__ == "__main__":
    count = migrate()
    print(f"Migrated {count} stock inward entr{'y' if count == 1 else 'ies'}.")
