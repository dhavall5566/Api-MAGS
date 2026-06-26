from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import PurchaseOrder
from app.services.db_helpers import (
    delete_entity,
    normalize_purchase_order_data,
    purchase_order_rows_as_dicts,
    upsert_entity,
)

router = APIRouter(prefix="/api/purchase-orders", tags=["purchase-orders"])


@router.get("")
def list_purchase_orders(db: Session = Depends(get_db)):
    rows = db.query(PurchaseOrder).all()
    return {"purchaseOrders": purchase_order_rows_as_dicts(rows)}


@router.post("")
def create_purchase_order(body: dict, db: Session = Depends(get_db)):
    if not body.get("id"):
        raise HTTPException(status_code=400, detail="id is required")
    saved = upsert_entity(db, PurchaseOrder, normalize_purchase_order_data(body))
    return {"purchaseOrder": saved}


@router.put("/{order_id}")
def update_purchase_order(order_id: str, body: dict, db: Session = Depends(get_db)):
    if body.get("id") and body["id"] != order_id:
        raise HTTPException(status_code=400, detail="id mismatch")
    body["id"] = order_id
    row = db.get(PurchaseOrder, order_id)
    if not row:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    saved = upsert_entity(db, PurchaseOrder, normalize_purchase_order_data(body))
    return {"purchaseOrder": saved}


@router.delete("/{order_id}")
def remove_purchase_order(order_id: str, db: Session = Depends(get_db)):
    if not delete_entity(db, PurchaseOrder, order_id):
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return {"ok": True, "id": order_id}
