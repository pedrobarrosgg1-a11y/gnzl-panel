"""Consultas de conversões sincronizadas pela API."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.conversion import Order


def existing_orders(
    session: Session,
    *,
    data_source: str,
    dedup_keys: set[str],
) -> dict[str, Order]:
    """Pedidos da origem indexados por ``dedup_key``.

    A fonte faz parte da consulta: o mesmo pedido vindo de CSV e de Shopee é
    mantido como registros separados, por decisão do modelo de dados.
    """
    if not dedup_keys:
        return {}
    orders = session.scalars(
        select(Order).where(
            Order.data_source == data_source,
            Order.dedup_key.in_(dedup_keys),
        )
    ).all()
    return {order.dedup_key: order for order in orders}
