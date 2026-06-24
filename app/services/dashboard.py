from datetime import datetime

MONTH_ORDER = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

VALID_TIMEFRAMES = {
    "today",
    "week",
    "month",
    "quarter",
    "year",
    "financial-year",
}


def start_of_day(dt: datetime) -> datetime:
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def end_of_day(dt: datetime) -> datetime:
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999)


def month_index(label: str) -> int:
    try:
        return MONTH_ORDER.index(label)
    except ValueError:
        return 0


def month_start(year: int, label: str) -> datetime:
    return start_of_day(datetime(year, month_index(label) + 1, 1))


def month_end(year: int, label: str) -> datetime:
    next_month = month_index(label) + 2
    year_adj = year
    if next_month > 12:
        next_month = 1
        year_adj += 1
    return end_of_day(datetime(year_adj, next_month, 1) - __import__("datetime").timedelta(days=1))


def overlap_ratio(range_start: datetime, range_end: datetime, period_start: datetime, period_end: datetime) -> float:
    start = max(range_start.timestamp(), period_start.timestamp())
    end = min(range_end.timestamp(), period_end.timestamp())
    if end < start:
        return 0.0
    overlap_ms = (end - start) * 1000 + 1
    period_ms = (period_end.timestamp() - period_start.timestamp()) * 1000 + 1
    return min(1.0, overlap_ms / period_ms)


def get_date_range_for_timeframe(timeframe: str, reference: datetime | None = None):
    ref = reference or datetime.now()
    start = start_of_day(ref)
    end = end_of_day(ref)

    if timeframe == "today":
        return start, end
    if timeframe == "week":
        weekday = ref.weekday()
        week_start = start_of_day(ref.replace(day=ref.day - weekday))
        week_end = end_of_day(week_start.replace(day=week_start.day + 6))
        return week_start, week_end
    if timeframe == "month":
        month_start_dt = start_of_day(ref.replace(day=1))
        next_month = month_start_dt.replace(month=month_start_dt.month % 12 + 1, day=1)
        if month_start_dt.month == 12:
            next_month = month_start_dt.replace(year=month_start_dt.year + 1, month=1, day=1)
        month_end_dt = end_of_day(next_month - __import__("datetime").timedelta(days=1))
        return month_start_dt, month_end_dt
    if timeframe == "quarter":
        quarter = (ref.month - 1) // 3
        q_start_month = quarter * 3 + 1
        q_start = start_of_day(ref.replace(month=q_start_month, day=1))
        q_end_month = q_start_month + 2
        q_end = end_of_day(
            datetime(q_start.year + (1 if q_end_month > 12 else 0), (q_end_month % 12) + 1, 1)
            - __import__("datetime").timedelta(days=1)
        )
        return q_start, q_end
    if timeframe == "year":
        year_start = start_of_day(ref.replace(month=1, day=1))
        year_end = end_of_day(ref.replace(month=12, day=31))
        return year_start, year_end

    # financial-year (Apr–Mar)
    fy_start_year = ref.year if ref.month >= 4 else ref.year - 1
    fy_start = start_of_day(datetime(fy_start_year, 4, 1))
    fy_end = end_of_day(datetime(fy_start_year + 1, 3, 31))
    return fy_start, fy_end


def scale_monthly_row(row: dict, ratio: float) -> dict:
    if ratio >= 0.999:
        return row
    return {
        **row,
        "inward": round(row["inward"] * ratio),
        "outward": round(row["outward"] * ratio),
        "coating": round(row["coating"] * ratio),
    }


def scale_consumption_row(row: dict, ratio: float) -> dict:
    if ratio >= 0.999:
        return row
    return {**row, "consumption": round(row["consumption"] * ratio)}


def filter_monthly_movement(rows: list[dict], range_start: datetime, range_end: datetime, year: int) -> list[dict]:
    result = []
    for row in rows:
        ratio = overlap_ratio(
            range_start,
            range_end,
            month_start(year, row["month"]),
            month_end(year, row["month"]),
        )
        if ratio > 0:
            result.append(scale_monthly_row(row, ratio))
    return result


def filter_consumption_trends(rows: list[dict], range_start: datetime, range_end: datetime, reference: datetime) -> list[dict]:
    total_weeks = len(rows)
    if total_weeks == 0:
        return rows

    anchor_end = end_of_day(reference)
    week_ms = 7 * 24 * 60 * 60 * 1000
    window_start = datetime.fromtimestamp(anchor_end.timestamp() - (total_weeks * week_ms / 1000) + 0.001)

    result = []
    for index, row in enumerate(rows):
        week_start = datetime.fromtimestamp(window_start.timestamp() + index * week_ms / 1000)
        week_end = end_of_day(datetime.fromtimestamp(week_start.timestamp() + 6 * 24 * 60 * 60))
        ratio = overlap_ratio(range_start, range_end, week_start, week_end)
        if ratio > 0:
            result.append(scale_consumption_row(row, ratio))
    return result


def period_ratio(range_start: datetime, range_end: datetime, reference: datetime) -> float:
    fy_start, fy_end = get_date_range_for_timeframe("financial-year", reference)
    selected_days = (range_end.timestamp() - range_start.timestamp()) / 86400 + 1
    fy_days = (fy_end.timestamp() - fy_start.timestamp()) / 86400 + 1
    return min(1.0, selected_days / fy_days)


def sum_monthly(rows: list[dict], key: str) -> int:
    return sum(row.get(key, 0) for row in rows)


def sum_consumption(rows: list[dict]) -> int:
    return sum(row.get("consumption", 0) for row in rows)


def sum_colors(rows: list[dict]) -> int:
    return sum(row.get("count", 0) for row in rows)


def scale_colors(rows: list[dict], ratio: float) -> list[dict]:
    if ratio >= 0.999:
        return rows
    return [{**row, "count": max(1, round(row["count"] * ratio))} for row in rows]


def build_dashboard_payload(timeframe: str, config: dict) -> dict:
    reference = datetime.now()
    range_start, range_end = get_date_range_for_timeframe(timeframe, reference)
    year = reference.year

    base_stats = config.get("dashboard_stats", {})
    charts = config.get("dashboard_charts", {})
    notifications = config.get("notifications", [])
    recent_transactions = config.get("recent_transactions", [])

    monthly = filter_monthly_movement(charts.get("monthlyStockMovement", []), range_start, range_end, year)
    consumption = filter_consumption_trends(charts.get("consumptionTrends", []), range_start, range_end, reference)

    coating_total = sum_monthly(monthly, "coating")
    coating_ratio = period_ratio(range_start, range_end, reference)
    color_rows = charts.get("colorDistribution", [])
    color_total = sum_colors(color_rows)
    scaled_colors = (
        scale_colors(color_rows, coating_total / max(color_total, 1))
        if coating_total > 0
        else scale_colors(color_rows, coating_ratio)
    )

    stats = {
        "totalProfiles": base_stats.get("totalProfiles", 0),
        "availableStock": base_stats.get("availableStock", 0),
        "lowStockProfiles": base_stats.get("lowStockProfiles", 0),
        "totalConsumption": sum_consumption(consumption)
        or round((base_stats.get("totalConsumption", 0) or 0) * coating_ratio),
        "pendingCoating": max(0, round((base_stats.get("pendingCoating", 0) or 0) * coating_ratio)),
        "completedCoating": max(0, round((base_stats.get("completedCoating", 0) or 0) * coating_ratio)),
        "scrapQuantity": max(0, round((base_stats.get("scrapQuantity", 0) or 0) * coating_ratio)),
    }

    return {
        **stats,
        "range": timeframe,
        "recentTransactions": recent_transactions,
        "stats": stats,
        "charts": {
            "inventoryOverview": charts.get("inventoryOverview", []),
            "monthlyStockMovement": monthly,
            "consumptionTrends": consumption if consumption else charts.get("consumptionTrends", []),
            "colorDistribution": scaled_colors,
        },
        "notifications": notifications,
    }
