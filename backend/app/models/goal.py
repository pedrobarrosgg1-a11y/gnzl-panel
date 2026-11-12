"""Metas de desempenho por período."""

from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import utcnow
from app.database.base import Base

GOAL_METRICS = ("commission_cents", "sales_cents", "orders", "clicks")


class Goal(Base):
    """Meta de uma métrica em um período fechado.

    O progresso não é persistido: é calculado a partir dos pedidos e cliques no
    momento da consulta, para não ficar desatualizado após uma importação.
    """

    __tablename__ = "goals"
    __table_args__ = (
        UniqueConstraint(
            "period_start", "period_end", "metric", name="uq_goals_period_metric"
        ),
        CheckConstraint("period_end >= period_start", name="period_order"),
        CheckConstraint("target_value > 0", name="target_positive"),
        CheckConstraint(
            "metric IN ('commission_cents', 'sales_cents', 'orders', 'clicks')",
            name="metric",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    metric: Mapped[str] = mapped_column(String(30), nullable=False)
    target_value: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )
