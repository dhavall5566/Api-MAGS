"""Seed PostgreSQL database from exported MAGS-Window mock data JSON files."""

from __future__ import annotations

import json
from pathlib import Path

from app.database import SessionLocal, init_db
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
from app.services.db_helpers import clear_all_data

SEED_DIR = Path(__file__).resolve().parent / "data"


def load_json(name: str):
    path = SEED_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run from MAGS-Window-: npx tsx scripts/export-seed-data.ts"
        )
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def seed_entity_table(db, model, items: list[dict]) -> int:
    count = 0
    for item in items:
        entity_id = item.get("id")
        if not entity_id:
            continue
        db.merge(model(id=entity_id, data=item))
        count += 1
    return count


def run_seed() -> None:
    init_db()
    db = SessionLocal()

    try:
        clear_all_data(db)

        counts = {
            "profiles": seed_entity_table(db, Profile, load_json("profiles")),
            "users": seed_entity_table(db, User, load_json("users")),
            "vendors": seed_entity_table(db, Vendor, load_json("vendors")),
            "series": seed_entity_table(db, SeriesName, load_json("series")),
            "stock_inward": seed_entity_table(db, StockInward, load_json("stock_inward")),
            "stock_ledger": seed_entity_table(db, StockLedgerEntry, load_json("stock_ledger")),
            "consumption": seed_entity_table(db, Consumption, load_json("consumption")),
            "powder_coating": seed_entity_table(db, PowderCoating, load_json("powder_coating")),
            "scrap": seed_entity_table(db, Scrap, load_json("scrap")),
            "challans": seed_entity_table(db, Challan, load_json("challans")),
            "purchase_orders": seed_entity_table(db, PurchaseOrder, load_json("purchase_orders")),
        }

        config_entries = {
            "dashboard_stats": load_json("dashboard_stats"),
            "dashboard_charts": load_json("dashboard_charts"),
            "notifications": load_json("notifications"),
            "recent_transactions": load_json("recent_transactions"),
            "monthlyStockMovement": load_json("monthlyStockMovement"),
            "consumptionTrends": load_json("consumptionTrends"),
            "colorDistribution": load_json("colorDistribution"),
            "inventoryByCategory": load_json("inventoryByCategory"),
            "reportSummary": load_json("reportSummary"),
        }

        for key, data in config_entries.items():
            db.merge(AppConfig(key=key, data=data))

        db.commit()

        print("Database seeded successfully:")
        for name, count in counts.items():
            print(f"  {name}: {count}")
        print(f"  app_config: {len(config_entries)} keys")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
