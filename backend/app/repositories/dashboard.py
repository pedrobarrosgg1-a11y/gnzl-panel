"""Consultas agregadas do dashboard.

As somas consideram apenas pedidos aprovados, mas os cliques consideram todas
as linhas do período: um clique aconteceu mesmo que o pedido tenha sido
cancelado depois. Pedidos são contados por ``external_order_id`` distinto, não
por linha, porque um pedido com vários itens continua sendo um pedido.

O recorte por dia é feito no fuso local (UTC-3 fixo). O agrupamento usa a
função ``date()`` do SQLite, que é o banco do projeto, com o mesmo offset
documentado em ``app.core.time``.
"""

from datetime import date, datetime

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.core.time import LOCAL_UTC_OFFSET_HOURS
from app.models.conversion import Click, Order

APPROVED_STATUS_GROUP = "approved"


def order_totals(
    session: Session, *, source: str, start: datetime, end: datetime
) -> tuple[int, int, int]:
    """Vendas, comissão e pedidos distintos do período."""
    row = session.execute(
        select(
            func.coalesce(func.sum(Order.sales_cents), 0),
            func.coalesce(func.sum(Order.commission_cents), 0),
            func.count(distinct(Order.external_order_id)),
        ).where(*_order_filters(source, start, end))
    ).one()
    return int(row[0]), int(row[1]), int(row[2])


def click_total(
    session: Session, *, source: str, start: datetime, end: datetime
) -> int:
    total = session.scalar(
        select(func.count(Click.id)).where(*_click_filters(source, start, end))
    )
    return int(total or 0)


def daily_orders(
    session: Session, *, source: str, start: datetime, end: datetime
) -> dict[date, tuple[int, int, int]]:
    """Vendas, comissão e pedidos por dia local; dias sem venda não aparecem."""
    local_day = _local_day(Order.ordered_at)
    rows = session.execute(
        select(
            local_day,
            func.coalesce(func.sum(Order.sales_cents), 0),
            func.coalesce(func.sum(Order.commission_cents), 0),
            func.count(distinct(Order.external_order_id)),
        )
        .where(*_order_filters(source, start, end))
        .group_by(local_day)
    ).all()
    return {
        date.fromisoformat(str(row[0])): (int(row[1]), int(row[2]), int(row[3]))
        for row in rows
    }


def daily_clicks(
    session: Session, *, source: str, start: datetime, end: datetime
) -> dict[date, int]:
    local_day = _local_day(Click.clicked_at)
    rows = session.execute(
        select(local_day, func.count(Click.id))
        .where(*_click_filters(source, start, end))
        .group_by(local_day)
    ).all()
    return {date.fromisoformat(str(row[0])): int(row[1]) for row in rows}


def top_sub_ids(
    session: Session, *, source: str, start: datetime, end: datetime, limit: int
) -> list[tuple[str | None, int, int, int]]:
    """Sub IDs ordenados por comissão; ``None`` é o grupo sem atribuição."""
    rows = session.execute(
        select(
            Order.sub_id_1,
            func.coalesce(func.sum(Order.sales_cents), 0),
            func.coalesce(func.sum(Order.commission_cents), 0),
            func.count(distinct(Order.external_order_id)),
        )
        .where(*_order_filters(source, start, end))
        .group_by(Order.sub_id_1)
        .order_by(
            func.sum(Order.commission_cents).desc(),
            func.sum(Order.sales_cents).desc(),
            Order.sub_id_1.asc(),
        )
        .limit(limit)
    ).all()
    return [
        (row[0], int(row[1]), int(row[2]), int(row[3])) for row in rows
    ]


def clicks_by_sub_id(
    session: Session, *, source: str, start: datetime, end: datetime
) -> dict[str | None, int]:
    rows = session.execute(
        select(Click.sub_id_1, func.count(Click.id))
        .where(*_click_filters(source, start, end))
        .group_by(Click.sub_id_1)
    ).all()
    return {row[0]: int(row[1]) for row in rows}


def top_items(
    session: Session, *, source: str, start: datetime, end: datetime, limit: int
) -> list[tuple[int, str | None, int, int, int]]:
    """Itens ordenados por comissão, com o título mais recente conhecido.

    Linhas sem ``external_item_id`` ficam fora: não há identidade para agrupar.
    """
    rows = session.execute(
        select(
            Order.external_item_id,
            func.coalesce(func.sum(Order.sales_cents), 0),
            func.coalesce(func.sum(Order.commission_cents), 0),
            func.count(distinct(Order.external_order_id)),
        )
        .where(
            *_order_filters(source, start, end),
            Order.external_item_id.is_not(None),
        )
        .group_by(Order.external_item_id)
        .order_by(
            func.sum(Order.commission_cents).desc(),
            func.sum(Order.sales_cents).desc(),
            Order.external_item_id.asc(),
        )
        .limit(limit)
    ).all()

    titles = _latest_titles(
        session, source=source, item_ids=[int(row[0]) for row in rows]
    )
    return [
        (
            int(row[0]),
            titles.get(int(row[0])),
            int(row[1]),
            int(row[2]),
            int(row[3]),
        )
        for row in rows
    ]


def _latest_titles(
    session: Session, *, source: str, item_ids: list[int]
) -> dict[int, str]:
    if not item_ids:
        return {}
    rows = session.execute(
        select(Order.external_item_id, Order.title)
        .where(
            Order.data_source == source,
            Order.external_item_id.in_(item_ids),
            Order.title.is_not(None),
        )
        .order_by(Order.ordered_at.desc(), Order.id.desc())
    ).all()
    titles: dict[int, str] = {}
    for item_id, title in rows:
        titles.setdefault(int(item_id), str(title))
    return titles


def _local_day(column):
    """Dia local de uma coluna UTC, no formato ``AAAA-MM-DD`` do SQLite."""
    return func.date(column, f"{LOCAL_UTC_OFFSET_HOURS:+d} hours")


def _order_filters(source: str, start: datetime, end: datetime) -> tuple:
    return (
        Order.data_source == source,
        Order.status_group == APPROVED_STATUS_GROUP,
        Order.ordered_at >= start,
        Order.ordered_at < end,
    )


def _click_filters(source: str, start: datetime, end: datetime) -> tuple:
    return (
        Click.data_source == source,
        Click.clicked_at >= start,
        Click.clicked_at < end,
    )
