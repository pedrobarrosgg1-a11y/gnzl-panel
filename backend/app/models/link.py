"""Lotes de geração e links de afiliado."""

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

from app.core.constants import SUB_ID_MAX_LENGTH
from app.core.time import utcnow
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.product import Product, ProductList

DESTINATION_TYPES = ("product", "list")
BATCH_STATUSES = ("pending", "running", "completed", "partial", "failed")
LINK_STATUSES = ("active", "replaced")
ITEM_STATUSES = ("pending", "success", "failed", "skipped")


def _sub_id_check(column: str) -> CheckConstraint:
    """Formato canônico: minúsculas, dígitos e hífen. Sem acento, espaço ou maiúscula."""
    return CheckConstraint(
        f"{column} IS NULL OR ("
        f"{column} NOT GLOB '*[^a-z0-9-]*' "
        f"AND length({column}) BETWEEN 1 AND {SUB_ID_MAX_LENGTH})",
        name=f"{column}_format",
    )


class LinkBatch(Base):
    """Agrupa uma operação de geração. Guarda o resultado real, inclusive parcial."""

    __tablename__ = "link_batches"
    __table_args__ = (
        CheckConstraint(
            "destination_type IN ('product', 'list')", name="destination_type"
        ),
        CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'partial', 'failed')",
            name="status",
        ),
        CheckConstraint(
            "(destination_type = 'product' AND product_list_id IS NULL) OR "
            "(destination_type = 'list' AND product_list_id IS NOT NULL)",
            name="destination_consistency",
        ),
        CheckConstraint(
            "total_items >= 0 AND successful_items >= 0 AND failed_items >= 0",
            name="counters_non_negative",
        ),
        CheckConstraint(
            "successful_items + failed_items <= total_items", name="counters_consistency"
        ),
        CheckConstraint("data_source IN ('demo', 'shopee', 'csv')", name="data_source"),
        _sub_id_check("sub_id_1"),
        _sub_id_check("sub_id_2"),
        _sub_id_check("sub_id_3"),
        _sub_id_check("sub_id_4"),
        _sub_id_check("sub_id_5"),
        Index("ix_link_batches_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str | None] = mapped_column(String(160))
    destination_type: Mapped[str] = mapped_column(String(20), nullable=False)
    product_list_id: Mapped[int | None] = mapped_column(
        ForeignKey("product_lists.id", ondelete="RESTRICT")
    )
    observation: Mapped[str | None] = mapped_column(Text)
    # Configuração da geração, guardada no lote para reexecutar itens falhos
    # com exatamente os mesmos Sub IDs.
    sub_id_1: Mapped[str | None] = mapped_column(String(SUB_ID_MAX_LENGTH))
    sub_id_2: Mapped[str | None] = mapped_column(String(SUB_ID_MAX_LENGTH))
    sub_id_3: Mapped[str | None] = mapped_column(String(SUB_ID_MAX_LENGTH))
    sub_id_4: Mapped[str | None] = mapped_column(String(SUB_ID_MAX_LENGTH))
    sub_id_5: Mapped[str | None] = mapped_column(String(SUB_ID_MAX_LENGTH))
    data_source: Mapped[str] = mapped_column(String(20), nullable=False, default="demo")
    total_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    successful_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)

    product_list: Mapped["ProductList | None"] = relationship()
    items: Mapped[list["LinkBatchItem"]] = relationship(
        back_populates="batch",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="LinkBatchItem.id",
    )


class LinkBatchItem(Base):
    """Um item do lote. Registra sucesso ou o motivo da falha, item a item."""

    __tablename__ = "link_batch_items"
    __table_args__ = (
        UniqueConstraint(
            "link_batch_id", "original_url", name="uq_link_batch_items_batch_url"
        ),
        CheckConstraint(
            "status IN ('pending', 'success', 'failed', 'skipped')", name="status"
        ),
        CheckConstraint("attempts >= 0", name="attempts_non_negative"),
        CheckConstraint(
            "status <> 'success' OR affiliate_link_id IS NOT NULL",
            name="success_requires_link",
        ),
        Index("ix_link_batch_items_batch_status", "link_batch_id", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    link_batch_id: Mapped[int] = mapped_column(
        ForeignKey("link_batches.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT")
    )
    original_url: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    affiliate_link_id: Mapped[int | None] = mapped_column(
        ForeignKey("affiliate_links.id", ondelete="SET NULL")
    )
    error_code: Mapped[str | None] = mapped_column(String(60))
    error_message: Mapped[str | None] = mapped_column(Text)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    batch: Mapped[LinkBatch] = relationship(back_populates="items")
    product: Mapped["Product | None"] = relationship()
    affiliate_link: Mapped["AffiliateLink | None"] = relationship()


class AffiliateLink(Base):
    """Um link gerado. Histórico imutável: regenerar cria outro e marca o antigo."""

    __tablename__ = "affiliate_links"
    __table_args__ = (
        UniqueConstraint("affiliate_url", name="uq_affiliate_links_affiliate_url"),
        CheckConstraint("status IN ('active', 'replaced')", name="status"),
        CheckConstraint("data_source IN ('demo', 'shopee', 'csv')", name="data_source"),
        CheckConstraint("affiliate_url <> ''", name="affiliate_url_not_empty"),
        _sub_id_check("sub_id_1"),
        _sub_id_check("sub_id_2"),
        _sub_id_check("sub_id_3"),
        _sub_id_check("sub_id_4"),
        _sub_id_check("sub_id_5"),
        Index("ix_affiliate_links_created_at", "created_at"),
        Index("ix_affiliate_links_sub_id_1", "sub_id_1"),
        Index("ix_affiliate_links_sub_id_2", "sub_id_2"),
        Index("ix_affiliate_links_sub_id_3", "sub_id_3"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), index=True
    )
    link_batch_id: Mapped[int | None] = mapped_column(
        ForeignKey("link_batches.id", ondelete="SET NULL"), index=True
    )
    original_url: Mapped[str] = mapped_column(Text, nullable=False)
    affiliate_url: Mapped[str] = mapped_column(Text, nullable=False)
    sub_id_1: Mapped[str | None] = mapped_column(String(SUB_ID_MAX_LENGTH))
    sub_id_2: Mapped[str | None] = mapped_column(String(SUB_ID_MAX_LENGTH))
    sub_id_3: Mapped[str | None] = mapped_column(String(SUB_ID_MAX_LENGTH))
    sub_id_4: Mapped[str | None] = mapped_column(String(SUB_ID_MAX_LENGTH))
    sub_id_5: Mapped[str | None] = mapped_column(String(SUB_ID_MAX_LENGTH))
    observation: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    replaced_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("affiliate_links.id", ondelete="SET NULL")
    )
    data_source: Mapped[str] = mapped_column(String(20), nullable=False, default="demo")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    product: Mapped["Product | None"] = relationship()
    batch: Mapped[LinkBatch | None] = relationship()
    replaced_by: Mapped["AffiliateLink | None"] = relationship(remote_side="AffiliateLink.id")
