from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import SessionLocal, init_db
from app.services.seed_sync import sync_all_seed_data
from app.routers import (
    app_settings,
    challans,
    consumption,
    dashboard,
    notifications,
    powder_coating,
    profiles,
    purchase_orders,
    reports,
    scrap,
    series,
    stock,
    stock_inward,
    uploads,
    users,
    vendors,
)

app = FastAPI(
    title="MAGS API",
    description="Backend API for MAGS Window aluminium profile management",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(app_settings.router)
app.include_router(profiles.router)
app.include_router(users.router)
app.include_router(vendors.router)
app.include_router(series.router)
app.include_router(stock.router)
app.include_router(stock_inward.router)
app.include_router(consumption.router)
app.include_router(powder_coating.router)
app.include_router(scrap.router)
app.include_router(challans.router)
app.include_router(purchase_orders.router)
app.include_router(dashboard.router)
app.include_router(notifications.router)
app.include_router(reports.router)
app.include_router(uploads.router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    db = SessionLocal()
    try:
        sync_all_seed_data(db)
    finally:
        db.close()


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "mags-api"}
