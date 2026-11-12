"""Acesso a dados das importações CSV."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.conversion import Click, Order
from app.models.import_log import ImportedRow, ImportLog


def list_page(
    session: Session,
    *,
    report_type: str | None,
    status: str | None,
    page: int,
    page_size: int,
) -> tuple[list[ImportLog], int]:
    conditions = []
    if report_type:
        conditions.append(ImportLog.report_type == report_type)
    if status:
        conditions.append(ImportLog.status == status)

    total = (
        session.scalar(select(func.count(ImportLog.id)).where(*conditions)) or 0
    )
    items = list(
        session.scalars(
            select(ImportLog)
            .where(*conditions)
            .order_by(ImportLog.created_at.desc(), ImportLog.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return items, total


def get_by_id(session: Session, import_id: int) -> ImportLog | None:
    return session.get(ImportLog, import_id)


def list_rows(
    session: Session,
    import_id: int,
    *,
    row_status: str | None,
    page: int,
    page_size: int,
) -> tuple[list[ImportedRow], int]:
    conditions = [ImportedRow.import_id == import_id]
    if row_status:
        conditions.append(ImportedRow.status == row_status)

    total = (
        session.scalar(select(func.count(ImportedRow.id)).where(*conditions)) or 0
    )
    rows = list(
        session.scalars(
            select(ImportedRow)
            .where(*conditions)
            .order_by(ImportedRow.row_number)
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return rows, total


def existing_order_ids(
    session: Session, dedup_keys: set[str]
) -> dict[str, int]:
    """Pedidos CSV já gravados, indexados por ``dedup_key``."""
    if not dedup_keys:
        return {}
    result = session.execute(
        select(Order.dedup_key, Order.id).where(
            Order.data_source == "csv",
            Order.dedup_key.in_(dedup_keys),
        )
    )
    return {key: order_id for key, order_id in result}


def existing_click_ids(
    session: Session, dedup_keys: set[str]
) -> dict[str, int]:
    """Cliques CSV já gravados, indexados por ``dedup_key``."""
    if not dedup_keys:
        return {}
    result = session.execute(
        select(Click.dedup_key, Click.id).where(
            Click.data_source == "csv",
            Click.dedup_key.in_(dedup_keys),
        )
    )
    return {key: click_id for key, click_id in result}
