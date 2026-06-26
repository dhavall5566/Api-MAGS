"""Remove lengthsInMeter from profiles.data JSONB."""

from app.database import SessionLocal
from app.models import Profile
from app.services.db_helpers import normalize_profile_data


def migrate() -> int:
    db = SessionLocal()
    updated = 0
    try:
        rows = db.query(Profile).all()
        for row in rows:
            normalized = normalize_profile_data(dict(row.data))
            if normalized != row.data:
                row.data = normalized
                updated += 1
        db.commit()
    finally:
        db.close()
    return updated


if __name__ == "__main__":
    count = migrate()
    print(f"Removed lengthsInMeter from {count} profile(s).")
