"""Persistência de produtos.

Produtos vistos em busca são gravados localmente: isso mantém o histórico
legível mesmo se o provedor mudar, e permite gerar links a partir de listas
sem depender da fonte no momento da geração. A identidade inclui a origem,
portanto um produto demo nunca sobrescreve um produto real.
"""

from collections.abc import Sequence

from sqlalchemy import func, select, tuple_
from sqlalchemy.orm import Session

from app.models.product import Product
from app.providers.base import ProductRecord


def _apply_fields(product: Product, record: ProductRecord) -> None:
    product.title = record.title
    product.image_url = record.image_url
    product.product_url = record.product_url
    product.price_cents = record.price_cents
    product.commission_rate_bp = record.commission_rate_bp
    product.sales = record.sales
    product.rating_x100 = record.rating_x100
    product.category = record.category


def upsert_records(session: Session, records: Sequence[ProductRecord]) -> list[Product]:
    """Insere ou atualiza os produtos e devolve na mesma ordem da entrada."""
    if not records:
        return []

    keys = {(record.item_id, record.shop_id, record.source) for record in records}
    existing_rows = session.scalars(
        select(Product).where(
            tuple_(Product.item_id, Product.shop_id, Product.data_source).in_(keys)
        )
    ).all()
    existing = {
        (product.item_id, product.shop_id, product.data_source): product
        for product in existing_rows
    }

    result: list[Product] = []
    for record in records:
        key = (record.item_id, record.shop_id, record.source)
        product = existing.get(key)
        if product is None:
            product = Product(
                item_id=record.item_id,
                shop_id=record.shop_id,
                data_source=record.source,
            )
            session.add(product)
            existing[key] = product
        _apply_fields(product, record)
        result.append(product)

    session.flush()
    return result


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
