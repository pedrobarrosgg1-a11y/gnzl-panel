"""Persistência de produtos.

Produtos vistos em busca são gravados localmente: isso mantém o histórico
legível mesmo se o provedor mudar, e permite gerar links a partir de listas
sem depender da fonte no momento da geração. A identidade inclui a origem,
portanto um produto demo nunca sobrescreve um produto real.
"""

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import func, select, tuple_
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.core.time import utcnow
from app.models.product import Product
from app.providers.base import ProductRecord


def _record_key(record: ProductRecord) -> tuple[int, int, str]:
    return (record.item_id, record.shop_id, record.source)


def _product_values(record: ProductRecord, now: datetime) -> dict:
    return {
        "item_id": record.item_id,
        "shop_id": record.shop_id,
        "title": record.title,
        "image_url": record.image_url,
        "product_url": record.product_url,
        "price_cents": record.price_cents,
        "commission_rate_bp": record.commission_rate_bp,
        "sales": record.sales,
        "rating_x100": record.rating_x100,
        "category": record.category,
        "data_source": record.source,
        "created_at": now,
        "updated_at": now,
    }


def upsert_records(session: Session, records: Sequence[ProductRecord]) -> list[Product]:
    """Insere ou atualiza os produtos e devolve na mesma ordem da entrada.

    A gravação usa ``INSERT ... ON CONFLICT`` em vez de "select e depois
    insert": duas buscas simultâneas na primeira visita ao banco podem enxergar
    o produto como inexistente ao mesmo tempo. O conflito é resolvido pelo
    próprio SQLite, sem derrubar uma das requisições com IntegrityError.
    """
    if not records:
        return []

    now = utcnow()
    statement = sqlite_insert(Product).values(
        [_product_values(record, now) for record in records]
    )
    statement = statement.on_conflict_do_update(
        index_elements=["item_id", "shop_id", "data_source"],
        set_={
            "title": statement.excluded.title,
            "image_url": statement.excluded.image_url,
            "product_url": statement.excluded.product_url,
            "price_cents": statement.excluded.price_cents,
            "commission_rate_bp": statement.excluded.commission_rate_bp,
            "sales": statement.excluded.sales,
            "rating_x100": statement.excluded.rating_x100,
            "category": statement.excluded.category,
            "updated_at": now,
        },
    )
    session.execute(statement)

    keys = {_record_key(record) for record in records}
    rows = session.scalars(
        select(Product).where(
            tuple_(Product.item_id, Product.shop_id, Product.data_source).in_(keys)
        )
    ).all()
    products = {
        (product.item_id, product.shop_id, product.data_source): product
        for product in rows
    }
    return [products[_record_key(record)] for record in records]


def get_by_id(session: Session, product_id: int) -> Product | None:
    return session.get(Product, product_id)


def get_by_ids(session: Session, product_ids: Sequence[int]) -> list[Product]:
    if not product_ids:
        return []
    return list(
        session.scalars(select(Product).where(Product.id.in_(set(product_ids)))).all()
    )


def distinct_categories(session: Session, source: str) -> list[str]:
    rows = session.scalars(
        select(Product.category)
        .where(Product.data_source == source, Product.category.is_not(None))
        .group_by(Product.category)
        .order_by(func.lower(Product.category))
    ).all()
    return [category for category in rows if category]
