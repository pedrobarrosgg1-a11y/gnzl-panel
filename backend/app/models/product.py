"""Produtos e listas de produtos."""

from datetime import datetime

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

from app.core.constants import LIST_NAME_MAX_LENGTH, PRODUCT_TITLE_MAX_LENGTH
from app.core.time import utcnow
from app.database.base import Base


class Product(Base):
    """Produto vindo de um provedor (demo, shopee ou csv).

    Valores monetários em centavos e percentuais em pontos-base para evitar
    erro de arredondamento em ponto flutuante.
    """

    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint(
            "item_id", "shop_id", "data_source", name="uq_products_item_shop_source"
        ),
        CheckConstraint("price_cents >= 0", name="price_non_negative"),
        CheckConstraint(
            "commission_rate_bp BETWEEN 0 AND 10000", name="commission_rate_range"
        ),
        CheckConstraint("sales IS NULL OR sales >= 0", name="sales_non_negative"),
        CheckConstraint(
            "rating_x100 IS NULL OR rating_x100 BETWEEN 0 AND 500",
            name="rating_range",
        ),
        CheckConstraint("data_source IN ('demo', 'shopee', 'csv')", name="data_source"),
        Index("ix_products_commission_rate_bp", "commission_rate_bp"),
        Index("ix_products_sales", "sales"),
        Index("ix_products_price_cents", "price_cents"),
        Index("ix_products_category", "category"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(Integer, nullable=False)
    shop_id: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(
        String(PRODUCT_TITLE_MAX_LENGTH), nullable=False
    )
    image_url: Mapped[str | None] = mapped_column(Text)
    product_url: Mapped[str | None] = mapped_column(Text)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    commission_rate_bp: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sales: Mapped[int | None] = mapped_column(Integer)
    rating_x100: Mapped[int | None] = mapped_column(Integer)
    category: Mapped[str | None] = mapped_column(String(120))
    data_source: Mapped[str] = mapped_column(String(20), nullable=False, default="demo")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )

    list_items: Mapped[list["ProductListItem"]] = relationship(back_populates="product")


class ProductList(Base):
    __tablename__ = "product_lists"
    __table_args__ = (
        UniqueConstraint("normalized_name", name="uq_product_lists_normalized_name"),
        CheckConstraint("length(trim(name)) > 0", name="name_not_empty"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(LIST_NAME_MAX_LENGTH), nullable=False)
    # Forma canônica usada para impedir "Black Friday" e "black friday" como
    # listas diferentes. Calculada pelo serviço, nunca digitada.
    normalized_name: Mapped[str] = mapped_column(
        String(LIST_NAME_MAX_LENGTH), nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )

    items: Mapped[list["ProductListItem"]] = relationship(
        back_populates="product_list",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class ProductListItem(Base):
    __tablename__ = "product_list_items"
    __table_args__ = (
        UniqueConstraint(
            "product_list_id", "product_id", name="uq_product_list_items_list_product"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_list_id: Mapped[int] = mapped_column(
        ForeignKey("product_lists.id", ondelete="CASCADE"), nullable=False
    )
    # RESTRICT: produto com histórico de links não pode desaparecer.
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    product_list: Mapped[ProductList] = relationship(back_populates="items")
    product: Mapped[Product] = relationship(back_populates="list_items")
