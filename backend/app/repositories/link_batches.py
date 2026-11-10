"""Acesso a dados dos lotes de geração."""

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.link import LinkBatch, LinkBatchItem
from app.models.product import Product


def create(
    session: Session,
    *,
    name: str | None,
    destination_type: str,
    product_list_id: int | None,
    observation: str | None,
    sub_ids: Sequence[str | None],
    data_source: str,
    total_items: int,
) -> LinkBatch:
    batch = LinkBatch(
        name=name,
        destination_type=destination_type,
        product_list_id=product_list_id,
        observation=observation,
        sub_id_1=sub_ids[0],
        sub_id_2=sub_ids[1],
        sub_id_3=sub_ids[2],
        sub_id_4=sub_ids[3],
        sub_id_5=sub_ids[4],
        data_source=data_source,
        total_items=total_items,
        successful_items=0,
        failed_items=0,
        status="pending",
    )
    session.add(batch)
    session.flush()
    return batch


def add_item(
    session: Session,
    batch: LinkBatch,
    *,
    product: Product,
    original_url: str,
) -> LinkBatchItem:
    item = LinkBatchItem(
        product=product,
        original_url=original_url,
        status="pending",
        attempts=0,
    )
    batch.items.append(item)
    session.flush()
    return item


def get_by_id(
    session: Session, batch_id: int, *, with_items: bool = False
) -> LinkBatch | None:
    stmt = select(LinkBatch).where(LinkBatch.id == batch_id)
    if with_items:
        stmt = stmt.options(
            selectinload(LinkBatch.items).selectinload(LinkBatchItem.product),
            selectinload(LinkBatch.items).selectinload(LinkBatchItem.affiliate_link),
        )
    return session.scalar(stmt)


def list_page(
    session: Session,
    *,
    status: str | None,
    data_source: str | None,
    page: int,
    page_size: int,
) -> tuple[list[LinkBatch], int]:
    conditions = []
    if status:
        conditions.append(LinkBatch.status == status)
    if data_source:
        conditions.append(LinkBatch.data_source == data_source)

    total = (
        session.scalar(
            select(func.count(LinkBatch.id)).where(*conditions)
        )
        or 0
    )
    batches = list(
        session.scalars(
            select(LinkBatch)
            .where(*conditions)
            .order_by(LinkBatch.created_at.desc(), LinkBatch.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return batches, total


def items_to_process(session: Session, batch_id: int) -> list[LinkBatchItem]:
    """Itens pendentes e itens que falharam — a base do retry."""
    return list(
        session.scalars(
            select(LinkBatchItem)
            .where(
                LinkBatchItem.link_batch_id == batch_id,
                LinkBatchItem.status.in_(("pending", "failed")),
            )
            .order_by(LinkBatchItem.id)
        ).all()
    )


def counts_by_status(session: Session, batch_id: int) -> dict[str, int]:
    rows = session.execute(
        select(LinkBatchItem.status, func.count(LinkBatchItem.id))
        .where(LinkBatchItem.link_batch_id == batch_id)
        .group_by(LinkBatchItem.status)
    ).all()
    return {status: count for status, count in rows}
