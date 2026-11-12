"""Pedidos e cliques importados de relatórios de conversão."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utcnow
from app.database.base import Base
from app.models.constraints import sub_id_format_constraint

if TYPE_CHECKING:
    from app.models.import_log import ImportLog
    from app.models.product import Product

DATA_SOURCES = ("demo", "shopee", "csv")
ORDER_STATUS_GROUPS = ("pending", "approved", "cancelled", "refunded", "unknown")


class Order(Base):
    """Uma linha de item do Conversion Report.

    O status bruto do relatório fica em ``status``; ``status_group`` é a
    classificação usada nas métricas. ``dedup_key`` identifica a linha dentro
    da origem para impedir importação duplicada.
    """

    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("data_source", "dedup_key", name="uq_orders_source_dedup"),
        CheckConstraint("quantity >= 0", name="quantity_non_negative"),
        CheckConstraint(
            "status_group IN ('pending', 'approved', 'cancelled', 'refunded', 'unknown')",
            name="status_group",
        ),
        CheckConstraint(
            "data_source IN ('demo', 'shopee', 'csv')", name="data_source"
        ),
        sub_id_format_constraint("sub_id_1"),
        sub_id_format_constraint("sub_id_2"),
        sub_id_format_constraint("sub_id_3"),
        sub_id_format_constraint("sub_id_4"),
        sub_id_format_constraint("sub_id_5"),
        Index("ix_orders_ordered_at", "ordered_at"),
        Index("ix_orders_status_group", "status_group"),
        Index("ix_orders_product_id", "product_id"),
        Index("ix_orders_sub_id_1", "sub_id_1"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_order_id: Mapped[str] = mapped_column(String(100), nullable=False)
    external_item_id: Mapped[int | None] = mapped_column(Integer)
    shop_id: Mapped[int | None] = mapped_column(Integer)
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL")
    )
    title: Mapped[str | None] = mapped_column(String(300))
    image_url: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(60), nullable=False)
    status_group: Mapped[str] = mapped_column(
        String(20), nullable=False, default="unknown"
    )
    ordered_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    sales_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    commission_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sub_id_1: Mapped[str | None] = mapped_column(String(64))
    sub_id_2: Mapped[str | None] = mapped_column(String(64))
    sub_id_3: Mapped[str | None] = mapped_column(String(64))
    sub_id_4: Mapped[str | None] = mapped_column(String(64))
    sub_id_5: Mapped[str | None] = mapped_column(String(64))
    channel: Mapped[str | None] = mapped_column(String(80))
    data_source: Mapped[str] = mapped_column(String(20), nullable=False)
    import_id: Mapped[int | None] = mapped_column(
        ForeignKey("import_logs.id", ondelete="SET NULL")
    )
    dedup_key: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )

    product: Mapped["Product | None"] = relationship()
    import_log: Mapped["ImportLog | None"] = relationship()


class Click(Base):
    """Uma linha do Click Report.

    Cliques não são vinculados a produto porque o relatório de cliques pode não
    identificar o item. A agregação por Sub ID e canal continua possível.
    """

    __tablename__ = "clicks"
    __table_args__ = (
        UniqueConstraint("data_source", "dedup_key", name="uq_clicks_source_dedup"),
        CheckConstraint(
            "data_source IN ('demo', 'shopee', 'csv')", name="data_source"
        ),
        sub_id_format_constraint("sub_id_1"),
        sub_id_format_constraint("sub_id_2"),
        sub_id_format_constraint("sub_id_3"),
        sub_id_format_constraint("sub_id_4"),
        sub_id_format_constraint("sub_id_5"),
        Index("ix_clicks_clicked_at", "clicked_at"),
        Index("ix_clicks_sub_id_1", "sub_id_1"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_click_id: Mapped[str | None] = mapped_column(String(120))
    clicked_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    region: Mapped[str | None] = mapped_column(String(80))
    channel: Mapped[str | None] = mapped_column(String(80))
    referrer: Mapped[str | None] = mapped_column(Text)
    sub_id_1: Mapped[str | None] = mapped_column(String(64))
    sub_id_2: Mapped[str | None] = mapped_column(String(64))
    sub_id_3: Mapped[str | None] = mapped_column(String(64))
    sub_id_4: Mapped[str | None] = mapped_column(String(64))
    sub_id_5: Mapped[str | None] = mapped_column(String(64))
    data_source: Mapped[str] = mapped_column(String(20), nullable=False)
    import_id: Mapped[int | None] = mapped_column(
        ForeignKey("import_logs.id", ondelete="SET NULL")
    )
    dedup_key: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    import_log: Mapped["ImportLog | None"] = relationship()
