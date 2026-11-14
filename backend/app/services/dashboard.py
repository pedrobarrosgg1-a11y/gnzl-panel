"""Montagem das métricas do dashboard.

O serviço não conhece HTTP: recebe a origem e o período em datas locais, consulta
o repositório e devolve números já derivados (conversão, ticket médio, variação
contra o período anterior). O endpoint apenas converte datas e serializa.

Regras de cálculo:
- vendas, comissão e pedidos consideram apenas pedidos aprovados;
- pedidos são ``external_order_id`` distintos, não linhas de item;
- cliques contam todas as linhas do período, inclusive de pedidos cancelados;
- conversão é ``pedidos / cliques`` em pontos-base; sem cliques, é ``None``;
- ticket médio é ``vendas / pedidos`` em centavos; sem pedidos, é ``None``;
- variação é ``(atual - anterior) / anterior`` em pontos-base; sem base
  anterior (anterior = 0), é ``None`` em vez de uma divisão sem sentido.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.core.constants import (
    DASHBOARD_TOP_LIMIT,
    DEFAULT_DASHBOARD_DAYS,
    MAX_DASHBOARD_DAYS,
)
from app.core.errors import ValidationError
from app.core.time import local_day_end_utc, local_day_start_utc, local_today
from app.models.conversion import DATA_SOURCES
from app.repositories import dashboard as dashboard_repository


@dataclass(frozen=True)
class Totals:
    sales_cents: int
    commission_cents: int
    orders: int
    clicks: int
    conversion_bp: int | None
    average_ticket_cents: int | None


@dataclass(frozen=True)
class Comparison:
    previous: int
    absolute: int
    variation_bp: int | None


@dataclass(frozen=True)
class DayPoint:
    day: date
    sales_cents: int
    commission_cents: int
    orders: int
    clicks: int


@dataclass(frozen=True)
class SubIdRow:
    sub_id_1: str | None
    sales_cents: int
    commission_cents: int
    orders: int
    clicks: int


@dataclass(frozen=True)
class ItemRow:
    external_item_id: int
    title: str | None
    sales_cents: int
    commission_cents: int
    orders: int


@dataclass(frozen=True)
class DashboardReport:
    source: str
    start: date
    end: date
    days: int
    previous_start: date
    previous_end: date
    totals: Totals
    previous_totals: Totals
    comparisons: dict[str, Comparison]
    daily: list[DayPoint]
    top_sub_ids: list[SubIdRow]
    top_items: list[ItemRow]


class DashboardService:
    def __init__(
        self,
        session: Session,
        *,
        today: Callable[[], date] = local_today,
    ) -> None:
        self._session = session
        self._today = today

    def report(
        self,
        source: str,
        start: date | None = None,
        end: date | None = None,
    ) -> DashboardReport:
        period_end = end or self._today()
        period_start = start or period_end - timedelta(
            days=DEFAULT_DASHBOARD_DAYS - 1
        )
        days = _validate_period(source, period_start, period_end)

        previous_end = period_start - timedelta(days=1)
        previous_start = previous_end - timedelta(days=days - 1)

        totals = self._totals(source, period_start, period_end)
        previous_totals = self._totals(source, previous_start, previous_end)

        return DashboardReport(
            source=source,
            start=period_start,
            end=period_end,
            days=days,
            previous_start=previous_start,
            previous_end=previous_end,
            totals=totals,
            previous_totals=previous_totals,
            comparisons={
                "sales_cents": _compare(
                    totals.sales_cents, previous_totals.sales_cents
                ),
                "commission_cents": _compare(
                    totals.commission_cents, previous_totals.commission_cents
                ),
                "orders": _compare(totals.orders, previous_totals.orders),
                "clicks": _compare(totals.clicks, previous_totals.clicks),
            },
            daily=self._daily(source, period_start, period_end),
            top_sub_ids=self._top_sub_ids(source, period_start, period_end),
            top_items=self._top_items(source, period_start, period_end),
        )

    def _totals(self, source: str, start: date, end: date) -> Totals:
        window_start = local_day_start_utc(start)
        window_end = local_day_end_utc(end)
        sales, commission, orders = dashboard_repository.order_totals(
            self._session, source=source, start=window_start, end=window_end
        )
        clicks = dashboard_repository.click_total(
            self._session, source=source, start=window_start, end=window_end
        )
        return Totals(
            sales_cents=sales,
            commission_cents=commission,
            orders=orders,
            clicks=clicks,
            conversion_bp=_basis_points(orders, clicks),
            average_ticket_cents=_rounded_ratio(sales, orders),
        )

    def _daily(self, source: str, start: date, end: date) -> list[DayPoint]:
        window_start = local_day_start_utc(start)
        window_end = local_day_end_utc(end)
        orders_by_day = dashboard_repository.daily_orders(
            self._session, source=source, start=window_start, end=window_end
        )
        clicks_by_day = dashboard_repository.daily_clicks(
            self._session, source=source, start=window_start, end=window_end
        )

        points: list[DayPoint] = []
        current = start
        while current <= end:
            sales, commission, orders = orders_by_day.get(current, (0, 0, 0))
            points.append(
                DayPoint(
                    day=current,
                    sales_cents=sales,
                    commission_cents=commission,
                    orders=orders,
                    clicks=clicks_by_day.get(current, 0),
                )
            )
            current += timedelta(days=1)
        return points

    def _top_sub_ids(self, source: str, start: date, end: date) -> list[SubIdRow]:
        window_start = local_day_start_utc(start)
        window_end = local_day_end_utc(end)
        clicks = dashboard_repository.clicks_by_sub_id(
            self._session, source=source, start=window_start, end=window_end
        )
        rows = dashboard_repository.top_sub_ids(
            self._session,
            source=source,
            start=window_start,
            end=window_end,
            limit=DASHBOARD_TOP_LIMIT,
        )
        return [
            SubIdRow(
                sub_id_1=sub_id,
                sales_cents=sales,
                commission_cents=commission,
                orders=orders,
                clicks=clicks.get(sub_id, 0),
            )
            for sub_id, sales, commission, orders in rows
        ]

    def _top_items(self, source: str, start: date, end: date) -> list[ItemRow]:
        rows = dashboard_repository.top_items(
            self._session,
            source=source,
            start=local_day_start_utc(start),
            end=local_day_end_utc(end),
            limit=DASHBOARD_TOP_LIMIT,
        )
        return [
            ItemRow(
                external_item_id=item_id,
                title=title,
                sales_cents=sales,
                commission_cents=commission,
                orders=orders,
            )
            for item_id, title, sales, commission, orders in rows
        ]


def _validate_period(source: str, start: date, end: date) -> int:
    if source not in DATA_SOURCES:
        raise ValidationError(
            "Origem desconhecida para o dashboard.",
            details={"source": source, "sources": list(DATA_SOURCES)},
        )

    days = (end - start).days + 1
    if days < 1:
        raise ValidationError(
            "A data inicial não pode ser posterior à data final.",
            details={"start": start.isoformat(), "end": end.isoformat()},
        )
    if days > MAX_DASHBOARD_DAYS:
        raise ValidationError(
            f"O período do dashboard é de no máximo {MAX_DASHBOARD_DAYS} dias.",
            details={
                "start": start.isoformat(),
                "end": end.isoformat(),
                "days": days,
                "max_days": MAX_DASHBOARD_DAYS,
            },
        )
    return days


def _compare(current: int, previous: int) -> Comparison:
    return Comparison(
        previous=previous,
        absolute=current - previous,
        variation_bp=_basis_points(current - previous, previous),
    )


def _basis_points(numerator: int, denominator: int) -> int | None:
    if denominator <= 0:
        return None
    return _divide_rounded(numerator * 10_000, denominator)


def _rounded_ratio(numerator: int, denominator: int) -> int | None:
    if denominator <= 0:
        return None
    return _divide_rounded(numerator, denominator)


def _divide_rounded(numerator: int, denominator: int) -> int:
    """Divisão inteira arredondada para longe do zero, sem ponto flutuante."""
    sign = -1 if (numerator < 0) != (denominator < 0) else 1
    absolute_numerator = abs(numerator)
    absolute_denominator = abs(denominator)
    return sign * (
        (2 * absolute_numerator + absolute_denominator)
        // (2 * absolute_denominator)
    )
