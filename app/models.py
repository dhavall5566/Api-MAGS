from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    data: Mapped[dict] = mapped_column(JSONB, nullable=False)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    data: Mapped[dict] = mapped_column(JSONB, nullable=False)


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    data: Mapped[dict] = mapped_column(JSONB, nullable=False)


class SeriesName(Base):
    __tablename__ = "series_names"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    data: Mapped[dict] = mapped_column(JSONB, nullable=False)


class StockInward(Base):
    __tablename__ = "stock_inward"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    data: Mapped[dict] = mapped_column(JSONB, nullable=False)


class StockLedgerEntry(Base):
    __tablename__ = "stock_ledger"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    data: Mapped[dict] = mapped_column(JSONB, nullable=False)


class Consumption(Base):
    __tablename__ = "consumption"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    data: Mapped[dict] = mapped_column(JSONB, nullable=False)


class PowderCoating(Base):
    __tablename__ = "powder_coating"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    data: Mapped[dict] = mapped_column(JSONB, nullable=False)


class Scrap(Base):
    __tablename__ = "scrap"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    data: Mapped[dict] = mapped_column(JSONB, nullable=False)


class Challan(Base):
    __tablename__ = "challans"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    data: Mapped[dict] = mapped_column(JSONB, nullable=False)


class AppConfig(Base):
    """Key-value store for dashboard stats, reports, notifications."""

    __tablename__ = "app_config"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    data: Mapped[dict | list] = mapped_column(JSONB, nullable=False)
