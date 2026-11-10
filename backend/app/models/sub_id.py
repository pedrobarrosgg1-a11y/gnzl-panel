"""Valores de Sub ID já usados, para autocomplete e padronização."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import SUB_ID_MAX_LENGTH
from app.core.time import utcnow
from app.database.base import Base

SUB_ID_DIMENSIONS = ("sub_id_1", "sub_id_2", "sub_id_3", "sub_id_4", "sub_id_5")


class SubIdValue(Base):
    __tablename__ = "sub_id_values"
    __table_args__ = (
        UniqueConstraint(
            "dimension", "normalized_value", name="uq_sub_id_values_dimension_value"
        ),
        CheckConstraint(
            "dimension IN ('sub_id_1', 'sub_id_2', 'sub_id_3', 'sub_id_4', 'sub_id_5')",
            name="dimension",
        ),
        CheckConstraint(
            "normalized_value NOT GLOB '*[^a-z0-9-]*' "
            f"AND length(normalized_value) BETWEEN 1 AND {SUB_ID_MAX_LENGTH}",
            name="normalized_value_format",
        ),
        CheckConstraint("usage_count >= 0", name="usage_count_non_negative"),
        Index("ix_sub_id_values_dimension_usage", "dimension", "usage_count"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dimension: Mapped[str] = mapped_column(String(20), nullable=False)
    normalized_value: Mapped[str] = mapped_column(String(SUB_ID_MAX_LENGTH), nullable=False)
    # Última forma digitada pelo usuário, apenas para exibição amigável.
    display_value: Mapped[str] = mapped_column(String(SUB_ID_MAX_LENGTH), nullable=False)
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime)
