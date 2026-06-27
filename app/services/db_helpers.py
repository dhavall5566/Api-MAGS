from sqlalchemy.orm import Session
import re
from datetime import date

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


def order_address_before_gst(data: dict, address_key: str, gst_key: str) -> dict:
    """Ensure address appears immediately before GST in API payloads."""
    if address_key not in data and gst_key not in data:
        return data

    reordered: dict = {}
    gst_value = data.get(gst_key)
    inserted_gst = False

    for key, value in data.items():
        if key == gst_key:
            continue
        reordered[key] = value
        if key == address_key and gst_key in data:
            reordered[gst_key] = gst_value
            inserted_gst = True

    if gst_key in data and not inserted_gst:
        reordered[gst_key] = gst_value

    return reordered


def normalize_challan_item(item: dict) -> dict:
    """Normalize challan line item; ``rate`` is R MTR RATE (₹/m) on powder coating challans."""
    normalized = dict(item)
    weight = normalized.get("weight")
    if weight is not None and weight != "":
        try:
            normalized["weight"] = round(max(0, float(weight)), 2)
        except (TypeError, ValueError):
            normalized["weight"] = 0
    else:
        normalized["weight"] = 0
    rate = normalized.get("rate")
    if rate is not None and rate != "":
        try:
            normalized["rate"] = round(max(0, float(rate)), 2)
        except (TypeError, ValueError):
            normalized.pop("rate", None)
    return normalized


def normalize_challan_data(data: dict) -> dict:
    normalized = dict(data)
    if isinstance(normalized.get("items"), list):
        normalized["items"] = [
            normalize_challan_item(item) for item in normalized["items"]
        ]
    if normalized.get("type") == "outward":
        if not normalized.get("projectName") and normalized.get("remarks"):
            normalized["projectName"] = normalized["remarks"]
        normalized.pop("remarks", None)
        total_bundles = normalized.get("totalBundles")
        if total_bundles is not None and total_bundles != "":
            try:
                normalized["totalBundles"] = max(0, int(total_bundles))
            except (TypeError, ValueError):
                normalized.pop("totalBundles", None)
        else:
            normalized.pop("totalBundles", None)
        total_weight_manual = normalized.get("totalWeightManual")
        if total_weight_manual is not None and total_weight_manual != "":
            try:
                normalized["totalWeightManual"] = round(max(0, float(total_weight_manual)), 2)
            except (TypeError, ValueError):
                normalized.pop("totalWeightManual", None)
        else:
            normalized.pop("totalWeightManual", None)
        total_no_of_profiles = normalized.get("totalNoOfProfiles")
        if total_no_of_profiles is not None and total_no_of_profiles != "":
            try:
                normalized["totalNoOfProfiles"] = max(0, int(total_no_of_profiles))
            except (TypeError, ValueError):
                normalized.pop("totalNoOfProfiles", None)
        else:
            normalized.pop("totalNoOfProfiles", None)
        items = normalized.get("items")
        if isinstance(items, list) and items:
            computed_weight = round(
                sum(
                    max(0, float(item.get("weight") or 0))
                    for item in items
                    if isinstance(item, dict)
                ),
                2,
            )
            if computed_weight > 0:
                normalized["totalWeightAllProfiles"] = computed_weight
            else:
                normalized.pop("totalWeightAllProfiles", None)
        else:
            normalized.pop("totalWeightAllProfiles", None)
        normalized.pop("outwardChallanVendorId", None)
        normalized.pop("outwardChallanVendorName", None)
    else:
        normalized.pop("totalBundles", None)
        normalized.pop("totalWeightManual", None)
        normalized.pop("totalNoOfProfiles", None)
        normalized.pop("totalWeightAllProfiles", None)
    if normalized.get("type") == "powder_coating":
        if not normalized.get("projectName") and normalized.get("remarks"):
            normalized["projectName"] = normalized["remarks"]
        normalized.pop("remarks", None)
        for key in ("outwardChallanVendorId", "outwardChallanVendorName"):
            value = normalized.get(key)
            if isinstance(value, str):
                value = value.strip()
                if value:
                    normalized[key] = value
                else:
                    normalized.pop(key, None)
            elif value is None:
                normalized.pop(key, None)
        coating_rate = normalized.get("coatingRate")
        if coating_rate is not None and coating_rate != "":
            try:
                normalized["coatingRate"] = round(max(0, float(coating_rate)), 4)
            except (TypeError, ValueError):
                normalized.pop("coatingRate", None)
        else:
            normalized.pop("coatingRate", None)
    else:
        normalized.pop("coatingRate", None)
        if normalized.get("type") != "powder_coating":
            normalized.pop("outwardChallanVendorId", None)
            normalized.pop("outwardChallanVendorName", None)
    return order_address_before_gst(normalized, "vendorAddress", "vendorGstNo")


def challan_rows_as_dicts(rows) -> list[dict]:
    return [normalize_challan_data(row.data) for row in rows]


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


MAGS_OUTWARD_CHALLAN_VENDOR_ID = "ven-mags-oc"

VENDOR_TYPE_LABELS = {
    "delivery": "Outward Challan",
    "outward_challan": "Powder Coating",
    "powder_coating": "Powder Coating Challan",
}


def normalize_vendor_data(data: dict) -> dict:
    """Normalize vendor JSON and validate vendor type."""
    allowed_types = {"delivery", "powder_coating", "outward_challan"}
    normalized = dict(data)
    vendor_type = str(normalized.get("vendorType") or "").strip()
    if vendor_type not in allowed_types:
        vendor_type = "delivery"
    vendor_id = str(normalized.get("id") or "").strip()
    if vendor_type == "outward_challan" and vendor_id != MAGS_OUTWARD_CHALLAN_VENDOR_ID:
        vendor_type = "delivery"
    normalized["vendorType"] = vendor_type
    normalized["vendorTypeLabel"] = VENDOR_TYPE_LABELS.get(vendor_type, vendor_type)
    for key in ("personName", "phoneNo", "email", "gstNo"):
        if normalized.get(key) is None:
            normalized[key] = ""
        elif isinstance(normalized.get(key), str):
            normalized[key] = normalized[key].strip()
    if isinstance(normalized.get("partyName"), str):
        normalized["partyName"] = normalized["partyName"].strip()
    if isinstance(normalized.get("partyAddress"), str):
        normalized["partyAddress"] = normalized["partyAddress"].strip()
    for key in (
        "challanHeaderName",
        "challanAddressLine1",
        "challanAddressLine2",
        "challanEmail",
        "challanPhone",
        "challanSignatoryLine",
    ):
        if isinstance(normalized.get(key), str):
            normalized[key] = normalized[key].strip()
    return normalized


def vendor_rows_as_dicts(rows) -> list[dict]:
    return [normalize_vendor_data(row.data) for row in rows]


def normalize_purchase_order_data(data: dict) -> dict:
    """Strip legacy vehicleNumber from purchase order JSON."""
    normalized = dict(data)
    normalized.pop("vehicleNumber", None)
    return order_address_before_gst(normalized, "vendorAddress", "gstNo")


def purchase_order_rows_as_dicts(rows) -> list[dict]:
    return [normalize_purchase_order_data(row.data) for row in rows]


def normalize_stock_inward_data(data: dict) -> dict:
    """Strip legacy fields and ensure stock inward JSON shape."""
    normalized = dict(data)
    normalized.pop("lengthFeet", None)
    normalized.pop("rate", None)

    total_weight = normalized.get("totalWeightKg")
    if total_weight is None:
        total_weight = normalized.get("weight")
    if total_weight is not None:
        normalized["totalWeightKg"] = total_weight
        normalized["weight"] = total_weight

    length = normalized.get("length")
    if length is not None:
        normalized["length"] = length

    for key in ("profileImage", "invoiceNo", "dyeCode"):
        if key in normalized and normalized[key] is not None:
            normalized[key] = str(normalized[key]).strip() or None

    if normalized.get("invoiceNo") is None:
        normalized.pop("invoiceNo", None)
    if normalized.get("profileImage") is None:
        normalized.pop("profileImage", None)

    normalized.setdefault("kgPerMeter", normalized.get("kgPerMeter") or 0)
    normalized.setdefault("quantity", normalized.get("quantity") or 0)
    normalized.setdefault("status", normalized.get("status") or "active")

    for optional_key in ("splitFromId", "splitFromInwardNo", "splitAt"):
        value = normalized.get(optional_key)
        if value is not None:
            normalized[optional_key] = str(value).strip() or None
        if not normalized.get(optional_key):
            normalized.pop(optional_key, None)

    return normalized


SPLIT_LENGTH_TOLERANCE = 0.0001


def normalize_stock_length(length: float) -> float:
    if not isinstance(length, (int, float)) or length <= 0:
        return 0.0
    return round(float(length) * 10000) / 10000


def generate_inward_nos(existing: list[dict], count: int) -> list[str]:
    year = date.today().year
    prefix = f"INW-{year}-"
    nums: list[int] = []
    for entry in existing:
        inward_no = entry.get("inwardNo") or ""
        match = re.match(r"INW-\d+-(\d+)", inward_no)
        if match:
            nums.append(int(match.group(1)))
    next_num = (max(nums) + 1) if nums else 1
    return [f"{prefix}{str(next_num + index).zfill(4)}" for index in range(count)]


def calculate_total_weight_kg(
    total_profiles: float, length_in_meter: float, kg_per_meter: float
) -> float:
    return round(total_profiles * length_in_meter * kg_per_meter * 100) / 100


def validate_stock_inward_split(parent: dict, pieces: list[dict]) -> str | None:
    if parent.get("status") == "split":
        return "This stock inward entry cannot be split."

    parent_length = normalize_stock_length(parent.get("length") or 0)
    parent_qty = float(parent.get("quantity") or 0)
    parent_weight = float(parent.get("totalWeightKg") or parent.get("weight") or 0)

    if parent_length <= SPLIT_LENGTH_TOLERANCE or parent_qty <= 0 or parent_weight <= 0:
        return "This stock inward entry cannot be split."

    if len(pieces) < 2:
        return "Enter at least two piece lengths."

    split_total = 0.0
    for piece in pieces:
        length = normalize_stock_length(piece.get("length") or 0)
        if length <= SPLIT_LENGTH_TOLERANCE:
            return "Each piece length must be greater than zero."
        if length >= parent_length - SPLIT_LENGTH_TOLERANCE:
            return "Each piece length must be less than the original length."
        split_total += length

    split_total = normalize_stock_length(split_total)
    if abs(split_total - parent_length) > SPLIT_LENGTH_TOLERANCE:
        return (
            f"Piece lengths must add up to {parent_length} m. "
            f"Current total: {split_total} m."
        )

    return None


def split_stock_inward_entry(
    db: Session, parent_id: str, pieces: list[dict]
) -> dict:
    row = db.get(StockInward, parent_id)
    if not row:
        raise ValueError("Stock inward entry not found")

    parent = normalize_stock_inward_data(dict(row.data))
    error = validate_stock_inward_split(parent, pieces)
    if error:
        raise ValueError(error)

    all_rows = db.query(StockInward).all()
    existing = [normalize_stock_inward_data(dict(item.data)) for item in all_rows]
    split_at = date.today().isoformat()
    parent_qty = float(parent.get("quantity") or 0)
    kg_per_meter = float(parent.get("kgPerMeter") or 0)
    inward_nos = generate_inward_nos(existing, len(pieces))

    children: list[dict] = []
    for index, piece in enumerate(pieces):
        length = normalize_stock_length(piece.get("length") or 0)
        total_weight_kg = calculate_total_weight_kg(parent_qty, length, kg_per_meter)
        child_id = piece.get("id") or f"si-{parent_id}-split-{index + 1}"
        children.append(
            normalize_stock_inward_data(
                {
                    "id": child_id,
                    "inwardNo": inward_nos[index],
                    "invoiceNo": parent.get("invoiceNo"),
                    "date": split_at,
                    "supplier": parent.get("supplier"),
                    "dyeCode": parent.get("dyeCode"),
                    "profileCode": parent.get("profileCode"),
                    "profileName": parent.get("profileName"),
                    "profileImage": parent.get("profileImage"),
                    "totalWeightKg": total_weight_kg,
                    "length": length,
                    "kgPerMeter": kg_per_meter,
                    "quantity": parent_qty,
                    "weight": total_weight_kg,
                    "splitFromId": parent.get("id"),
                    "splitFromInwardNo": parent.get("inwardNo"),
                    "splitAt": split_at,
                    "status": "active",
                    "remarks": parent.get("remarks"),
                }
            )
        )

    updated_parent = normalize_stock_inward_data(
        {
            **parent,
            "status": "split",
            "splitAt": split_at,
            "totalWeightKg": 0,
            "weight": 0,
            "quantity": 0,
        }
    )

    upsert_entity(db, StockInward, updated_parent)
    saved_children = [upsert_entity(db, StockInward, child) for child in children]
    db.commit()

    return {"updatedParent": updated_parent, "children": saved_children}


def stock_inward_rows_as_dicts(rows) -> list[dict]:
    return [normalize_stock_inward_data(row.data) for row in rows]


def upsert_entity(db: Session, model, item: dict) -> dict:
    return upsert_entities(db, model, [item])[0]


def upsert_entities(db: Session, model, items: list[dict]) -> list[dict]:
    if not items:
        return []

    try:
        for item in items:
            entity_id = item.get("id")
            if not entity_id:
                raise ValueError("Entity id is required")
            row = db.get(model, entity_id)
            if row:
                row.data = item
            else:
                db.add(model(id=entity_id, data=item))
        db.commit()
        for item in items:
            row = db.get(model, item["id"])
            if row:
                db.refresh(row)
        return items
    except Exception:
        db.rollback()
        raise


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
