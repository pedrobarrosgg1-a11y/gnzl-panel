"""Acesso a dados de listas de produtos."""

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.product import Product, ProductList, ProductListItem


def create(
    session: Session,
    *,
    name: str,
    normalized_name: str,
    description: str | None,
) -> ProductList:
    product_list = ProductList(
        name=name.strip(), normalized_name=normalized_name, description=description
    )
    session.add(product_list)
    session.flush()
    return product_list


def get_by_id(session: Session, list_id: int) -> ProductList | None:
    return session.get(ProductList, list_id)


def get_by_normalized_name(session: Session, normalized_name: str) -> ProductList | None:
    return session.scalar(
        select(ProductList).where(ProductList.normalized_name == normalized_name)
    )


def list_with_counts(session: Session) -> list[tuple[ProductList, int]]:
    rows = session.execute(
        select(ProductList, func.count(ProductListItem.id))
        .outerjoin(ProductListItem, ProductListItem.product_list_id == ProductList.id)
        .group_by(ProductList.id)
        .order_by(ProductList.created_at.desc(), ProductList.id.desc())
    ).all()
    return [(row[0], row[1]) for row in rows]


def items_of(session: Session, list_id: int) -> list[ProductListItem]:
    return list(
        session.scalars(
            select(ProductListItem)
            .where(ProductListItem.product_list_id == list_id)
            .options(selectinload(ProductListItem.product))
            .order_by(ProductListItem.created_at, ProductListItem.id)
        ).all()
    )


def existing_product_ids(session: Session, list_id: int) -> set[int]:
    return set(
        session.scalars(
            select(ProductListItem.product_id).where(
                ProductListItem.product_list_id == list_id
            )
        ).all()
    )


def add_items(session: Session, list_id: int, product_ids: Sequence[int]) -> int:
    added = 0
    for product_id in product_ids:
        session.add(ProductListItem(product_list_id=list_id, product_id=product_id))
        added += 1
    session.flush()
    return added


def remove_item(session: Session, list_id: int, product_id: int) -> bool:
    item = session.scalar(
        select(ProductListItem).where(
            ProductListItem.product_list_id == list_id,
            ProductListItem.product_id == product_id,
        )
    )
    if item is None:
        return False
    session.delete(item)
    session.flush()
    return True


def delete(session: Session, product_list: ProductList) -> None:
    session.delete(product_list)
    session.flush()


def count_items(session: Session, list_id: int) -> int:
    return (
        session.scalar(
            select(func.count(ProductListItem.id)).where(
                ProductListItem.product_list_id == list_id
            )
        )
        or 0
    )


def products_of(session: Session, list_id: int) -> list[Product]:
    return list(
        session.scalars(
            select(Product)
            .join(ProductListItem, ProductListItem.product_id == Product.id)
            .where(ProductListItem.product_list_id == list_id)
            .order_by(ProductListItem.created_at, ProductListItem.id)
        ).all()
    )
