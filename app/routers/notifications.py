from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.db_helpers import get_config, upsert_config

router = APIRouter(prefix="/api/notifications", tags=["notifications"])

EVENT_KEY = "event_notifications"
MAX_EVENTS = 200

ALLOWED_TYPES = {"info", "warning", "success", "error"}
ALLOWED_CATEGORIES = {
    "stock_low",
    "stock_out",
    "challan",
    "sync",
    "report",
    "stock_inward",
    "general",
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_events(db: Session) -> list:
    stored = get_config(db, EVENT_KEY, [])
    return stored if isinstance(stored, list) else []


def _save_events(db: Session, events: list) -> None:
    upsert_config(db, EVENT_KEY, events)


def _normalize_event(body: dict, *, existing: dict | None = None) -> dict:
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Expected JSON object")

    title = str(body.get("title") or existing.get("title") if existing else "").strip()
    message = str(body.get("message") or existing.get("message") if existing else "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="title is required")
    if not message:
        raise HTTPException(status_code=400, detail="message is required")

    notif_type = str(body.get("type") or (existing or {}).get("type") or "info")
    if notif_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Invalid notification type")

    category = body.get("category", (existing or {}).get("category"))
    if category is not None:
        category = str(category)
        if category not in ALLOWED_CATEGORIES:
            raise HTTPException(status_code=400, detail="Invalid notification category")

    return {
        "id": str(body.get("id") or (existing or {}).get("id") or uuid4()),
        "title": title,
        "message": message,
        "type": notif_type,
        "source": "event",
        "category": category,
        "href": body.get("href", (existing or {}).get("href")),
        "entityId": body.get("entityId", (existing or {}).get("entityId")),
        "read": bool(body.get("read", (existing or {}).get("read", False))),
        "createdAt": str(
            body.get("createdAt") or (existing or {}).get("createdAt") or _utc_now_iso()
        ),
    }


@router.get("")
def list_event_notifications(db: Session = Depends(get_db)):
    events = _load_events(db)
    normalized = [event for event in events if isinstance(event, dict)]
    normalized.sort(key=lambda item: item.get("createdAt", ""), reverse=True)
    return {"notifications": normalized}


@router.post("")
def create_event_notification(body: dict, db: Session = Depends(get_db)):
    notification = _normalize_event(body)
    events = _load_events(db)
    events = [notification, *events][:MAX_EVENTS]
    _save_events(db, events)
    db.commit()
    return {"notification": notification}


@router.patch("/{notification_id}/read")
def mark_notification_read(notification_id: str, db: Session = Depends(get_db)):
    events = _load_events(db)
    found = False
    updated: list = []
    for event in events:
        if not isinstance(event, dict):
            continue
        if event.get("id") == notification_id:
            found = True
            updated.append({**event, "read": True})
        else:
            updated.append(event)

    if not found:
        raise HTTPException(status_code=404, detail="Notification not found")

    _save_events(db, updated)
    db.commit()
    return {"ok": True}


@router.post("/mark-all-read")
def mark_all_notifications_read(db: Session = Depends(get_db)):
    events = _load_events(db)
    updated = [
        {**event, "read": True} if isinstance(event, dict) else event for event in events
    ]
    _save_events(db, updated)
    db.commit()
    return {"ok": True}
