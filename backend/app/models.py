from datetime import date, datetime, timezone
from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


class ForecastRun(Base):
    __tablename__ = "forecast_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    mode: Mapped[str] = mapped_column(String(24), default="trained")
    model_name: Mapped[str] = mapped_column(String(120), default="LightGBM")
    horizon_days: Mapped[int] = mapped_column(Integer, default=30)
    source_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    history_run_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)

    actuals: Mapped[list["DailyActual"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )
    forecasts: Mapped[list["ForecastPoint"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class DailyActual(Base):
    __tablename__ = "daily_actuals"
    __table_args__ = (
        UniqueConstraint("run_id", "date", "store_nbr", "family", name="uq_actual_series_day"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("forecast_runs.id", ondelete="CASCADE"), index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    store_nbr: Mapped[int] = mapped_column(Integer, index=True)
    family: Mapped[str] = mapped_column(String(120), index=True)
    sales: Mapped[float] = mapped_column(Float)
    run: Mapped[ForecastRun] = relationship(back_populates="actuals")


class ForecastPoint(Base):
    __tablename__ = "forecast_points"
    __table_args__ = (
        UniqueConstraint("run_id", "date", "store_nbr", "family", name="uq_forecast_series_day"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("forecast_runs.id", ondelete="CASCADE"), index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    store_nbr: Mapped[int] = mapped_column(Integer, index=True)
    family: Mapped[str] = mapped_column(String(120), index=True)
    forecast: Mapped[float] = mapped_column(Float)
    lower: Mapped[float | None] = mapped_column(Float, nullable=True)
    upper: Mapped[float | None] = mapped_column(Float, nullable=True)
    onpromotion: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_holiday: Mapped[bool] = mapped_column(default=False)
    run: Mapped[ForecastRun] = relationship(back_populates="forecasts")
