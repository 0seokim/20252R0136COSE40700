from sqlalchemy import String, Integer, Float, Date, DateTime, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, date
from app.database import Base

class ExchangeRate(Base):
    __tablename__ = "exchange_rates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    day: Mapped[date] = mapped_column(Date, nullable=False)               # YYYY-MM-DD
    currency: Mapped[str] = mapped_column(String(8), nullable=False)      # USD/EUR/JPY
    krw_per_unit: Mapped[float] = mapped_column(Float, nullable=False)    # 1 unit -> KRW
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("day", "currency", name="uq_exchange_day_currency"),
        Index("ix_exchange_day", "day"),
    )

class NewsArticle(Base):
    __tablename__ = "news_articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(1024), nullable=True)
    domain: Mapped[str] = mapped_column(String(255), nullable=True)
    seendate: Mapped[str] = mapped_column(String(32), nullable=True)  # GDELT format (e.g., YYYYMMDDHHMMSS)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
