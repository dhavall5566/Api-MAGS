"""Sync canonical seed JSON into the database on startup."""

import json
from collections.abc import Callable
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import (
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
)
from app.services.db_helpers import (
    normalize_profile_data,
    normalize_series_data,
    normalize_stock_inward_data,
    upsert_entities,
)

SEED_DIR = Path(__file__).resolve().parent.parent.parent / "seed" / "data"

ENTITY_SEEDS: list[tuple[str, type, Callable[[dict], dict] | None]] = [
    ("profiles", Profile, normalize_profile_data),
    ("users", User, None),
    ("series", SeriesName, normalize_series_data),
    ("stock_inward", StockInward, normalize_stock_inward_data),
    ("stock_ledger", StockLedgerEntry, None),
    ("consumption", Consumption, None),
    ("powder_coating", PowderCoating, None),
    ("scrap", Scrap, None),
    ("challans", Challan, None),
    ("purchase_orders", PurchaseOrder, None),
]


def _load_json(name: str) -> list[dict]:
    path = SEED_DIR / f"{name}.json"
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload if isinstance(payload, list) else []


def _sync_entity_list(db: Session, filename: str, model: type, normalizer) -> int:
    items = _load_json(filename)
    if not items:
        return 0
    if normalizer:
        items = [normalizer(item) for item in items]
    upsert_entities(db, model, items)
    db.commit()
    return len(items)


def sync_all_seed_data(db: Session) -> None:
    synced = {}
    for filename, model, normalizer in ENTITY_SEEDS:
        count = _sync_entity_list(db, filename, model, normalizer)
        if count:
            synced[filename] = count

    if synced:
        print("Seed sync:", ", ".join(f"{key}={value}" for key, value in synced.items()))
