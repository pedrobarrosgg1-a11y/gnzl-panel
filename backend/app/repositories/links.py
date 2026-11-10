"""Acesso a dados do histórico de links."""

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.link import AffiliateLink
from app.models.product import Product


def get_by_id(session: Session, link_id: int) -> AffiliateLink | None:
    return session.scalar(
        select(AffiliateLink)
        .where(AffiliateLink.id == link_id)
        .options(selectinload(AffiliateLink.product))
    )


def get_by_affiliate_url(session: Session, affiliate_url: str) -> AffiliateLink | None:
    return session.scalar(
        select(AffiliateLink).where(AffiliateLink.affiliate_url == affiliate_url)
    )


def search(
    session: Session,
    *,
    term: str | None,
    batch_id: int | None,
    status: str | None,
    sub_id_1: str | None,
    sub_id_2: str | None,
    sub_id_3: str | None,
    data_source: str | None,
    page: int,
    page_size: int,
) -> tuple[list[AffiliateLink], int]:
    conditions = []
    if batch_id is not None:
        conditions.append(AffiliateLink.link_batch_id == batch_id)
    if status:
        conditions.append(AffiliateLink.status == status)
    if sub_id_1:
        conditions.append(AffiliateLink.sub_id_1 == sub_id_1)
    if sub_id_2:
        conditions.append(AffiliateLink.sub_id_2 == sub_id_2)
    if sub_id_3:
        conditions.append(AffiliateLink.sub_id_3 == sub_id_3)
    if data_source:
        conditions.append(AffiliateLink.data_source == data_source)
    if term:
        needle = f"%{term.strip().lower()}%"
        conditions.append(
            or_(
                func.lower(AffiliateLink.original_url).like(needle),
                func.lower(AffiliateLink.affiliate_url).like(needle),
                func.lower(Product.title).like(needle),
            )
        )

    # O join é apenas para permitir buscar pelo título do produto. Como cada
    # link aponta para no máximo um produto, não há duplicação de linhas.
    base = select(AffiliateLink).outerjoin(Product, AffiliateLink.product_id == Product.id)
    total = (
        session.scalar(
            select(func.count(AffiliateLink.id))
            .outerjoin(Product, AffiliateLink.product_id == Product.id)
            .where(*conditions)
        )
        or 0
    )
    links = list(
        session.scalars(
            base.where(*conditions)
            .options(selectinload(AffiliateLink.product))
            .order_by(AffiliateLink.created_at.desc(), AffiliateLink.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return links, total
