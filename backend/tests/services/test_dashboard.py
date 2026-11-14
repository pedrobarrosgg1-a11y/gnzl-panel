"""Testes das agregações do dashboard."""

import uuid
from datetime import date, datetime

import pytest
from sqlalchemy.orm import Session

from app.core.errors import ValidationError
from app.models.conversion import Click, Order
from app.services.dashboard import DashboardService

NOVEMBER = (date(2026, 11, 1), date(2026, 11, 30))


def _order(
    session: Session,
    when: datetime,
    *,
    order_id: str = "A",
    item_id: int = 10,
    status_group: str = "approved",
    sales_cents: int = 0,
    commission_cents: int = 0,
    sub_id_1: str | None = None,
    source: str = "csv",
    title: str | None = None,
) -> Order:
    order = Order(
        external_order_id=order_id,
        external_item_id=item_id,
        status="Aprovado",
        status_group=status_group,
        ordered_at=when,
        quantity=1,
        sales_cents=sales_cents,
        commission_cents=commission_cents,
        sub_id_1=sub_id_1,
        title=title,
        data_source=source,
        dedup_key=f"order:{uuid.uuid4().hex}",
    )
    session.add(order)
    return order


def _click(
    session: Session,
    when: datetime,
    *,
    sub_id_1: str | None = None,
    source: str = "csv",
) -> Click:
    click = Click(
        clicked_at=when,
        sub_id_1=sub_id_1,
        data_source=source,
        dedup_key=f"click:{uuid.uuid4().hex}",
    )
    session.add(click)
    return click


def _report(session: Session):
    return DashboardService(session).report("csv", *NOVEMBER)


def test_totals_use_local_days_and_only_approved_orders(session: Session) -> None:
    _order(
        session,
        datetime(2026, 11, 1, 2, 59),
        order_id="antes",
        sales_cents=100,
        commission_cents=10,
    )
    _order(
        session,
        datetime(2026, 11, 1, 3, 0),
        order_id="A",
        item_id=10,
        sales_cents=1000,
        commission_cents=100,
        sub_id_1="instagram",
    )
    _order(
        session,
        datetime(2026, 11, 2, 10, 0),
        order_id="A",
        item_id=11,
        sales_cents=500,
        commission_cents=50,
        sub_id_1="instagram",
    )
    _order(
        session,
        datetime(2026, 11, 30, 23, 59, 59),
        order_id="B",
        item_id=20,
        sales_cents=2000,
        commission_cents=200,
        sub_id_1="youtube",
    )
    _order(
        session,
        datetime(2026, 11, 15, 10, 0),
        order_id="C",
        item_id=30,
        status_group="cancelled",
        sales_cents=9999,
        commission_cents=999,
    )
    _order(
        session,
        datetime(2026, 12, 1, 3, 0),
        order_id="depois",
        sales_cents=3000,
        commission_cents=300,
    )
    _order(
        session,
        datetime(2026, 11, 10, 10, 0),
        order_id="demo",
        source="demo",
        sales_cents=7777,
        commission_cents=777,
    )

    _click(session, datetime(2026, 11, 1, 3, 0), sub_id_1="instagram")
    _click(session, datetime(2026, 11, 3, 10, 0), sub_id_1="instagram")
    _click(session, datetime(2026, 11, 5, 10, 0), sub_id_1="tiktok")
    _click(session, datetime(2026, 11, 30, 23, 59, 59), sub_id_1="youtube")
    _click(session, datetime(2026, 11, 1, 2, 59), sub_id_1="instagram")
    _click(session, datetime(2026, 11, 10, 10, 0), sub_id_1="demo", source="demo")

    report = _report(session)

    assert report.days == 30
    assert report.totals.sales_cents == 3500
    assert report.totals.commission_cents == 350
    assert report.totals.orders == 2
    assert report.totals.clicks == 4
    assert report.totals.conversion_bp == 5000
    assert report.totals.average_ticket_cents == 1750


def test_daily_series_is_zero_filled_and_bucketed_by_local_day(
    session: Session,
) -> None:
    _order(
        session,
        datetime(2026, 11, 1, 3, 0),
        sales_cents=1000,
        commission_cents=100,
    )
    _click(session, datetime(2026, 11, 1, 3, 0))
    _click(session, datetime(2026, 11, 1, 3, 30))

    report = _report(session)

    assert len(report.daily) == 30
    assert report.daily[0].day == date(2026, 11, 1)
    assert report.daily[0].sales_cents == 1000
    assert report.daily[0].orders == 1
    assert report.daily[0].clicks == 2
    assert report.daily[1].sales_cents == 0
    assert report.daily[1].clicks == 0
    assert report.daily[-1].day == date(2026, 11, 30)


def test_order_at_utc_midnight_belongs_to_the_previous_local_day(
    session: Session,
) -> None:
    _order(session, datetime(2026, 11, 1, 2, 59), sales_cents=100)

    report = DashboardService(session).report(
        "csv", date(2026, 10, 31), date(2026, 10, 31)
    )

    assert report.totals.sales_cents == 100
    assert report.daily[0].day == date(2026, 10, 31)
    assert report.daily[0].sales_cents == 100


def test_previous_period_has_the_same_length_and_is_compared(
    session: Session,
) -> None:
    _order(
        session,
        datetime(2026, 10, 10, 10, 0),
        sales_cents=700,
        commission_cents=70,
    )
    _click(session, datetime(2026, 10, 10, 10, 0))
    _order(
        session,
        datetime(2026, 11, 10, 10, 0),
        sales_cents=3500,
        commission_cents=350,
        order_id="A",
    )
    _order(
        session,
        datetime(2026, 11, 11, 10, 0),
        sales_cents=0,
        commission_cents=0,
        order_id="B",
    )
    for index in range(4):
        _click(session, datetime(2026, 11, 10 + index, 10, 0))

    report = _report(session)

    assert report.previous_start == date(2026, 10, 2)
    assert report.previous_end == date(2026, 10, 31)
    assert report.previous_totals.sales_cents == 700
    assert report.previous_totals.orders == 1
    assert report.previous_totals.clicks == 1

    assert report.comparisons["sales_cents"].absolute == 2800
    assert report.comparisons["sales_cents"].variation_bp == 40000
    assert report.comparisons["orders"].absolute == 1
    assert report.comparisons["orders"].variation_bp == 10000
    assert report.comparisons["clicks"].absolute == 3
    assert report.comparisons["clicks"].variation_bp == 30000


def test_empty_period_returns_zeroes_and_no_derived_metric(
    session: Session,
) -> None:
    report = _report(session)

    assert report.totals.sales_cents == 0
    assert report.totals.orders == 0
    assert report.totals.clicks == 0
    assert report.totals.conversion_bp is None
    assert report.totals.average_ticket_cents is None
    assert report.comparisons["sales_cents"].variation_bp is None
    assert report.comparisons["clicks"].variation_bp is None
    assert len(report.daily) == 30
    assert all(point.sales_cents == 0 for point in report.daily)
    assert report.top_sub_ids == []
    assert report.top_items == []


def test_rankings_are_ordered_by_commission_and_include_unattributed_orders(
    session: Session,
) -> None:
    _order(
        session,
        datetime(2026, 11, 1, 10, 0),
        order_id="A",
        item_id=10,
        sub_id_1="instagram",
        sales_cents=1000,
        commission_cents=100,
        title="Fone antigo",
    )
    _order(
        session,
        datetime(2026, 11, 5, 10, 0),
        order_id="B",
        item_id=10,
        sub_id_1="instagram",
        sales_cents=2000,
        commission_cents=50,
        title="Fone novo",
    )
    _order(
        session,
        datetime(2026, 11, 6, 10, 0),
        order_id="C",
        item_id=20,
        sub_id_1="youtube",
        sales_cents=3000,
        commission_cents=200,
        title="Capa",
    )
    _order(
        session,
        datetime(2026, 11, 7, 10, 0),
        order_id="D",
        item_id=30,
        sales_cents=400,
        commission_cents=20,
        title="Sem sub id",
    )
    _click(session, datetime(2026, 11, 1, 10, 0), sub_id_1="instagram")
    _click(session, datetime(2026, 11, 2, 10, 0), sub_id_1="youtube")

    report = _report(session)

    assert [row.sub_id_1 for row in report.top_sub_ids] == [
        "youtube",
        "instagram",
        None,
    ]
    instagram = report.top_sub_ids[1]
    assert instagram.sales_cents == 3000
    assert instagram.commission_cents == 150
    assert instagram.orders == 2
    assert instagram.clicks == 1

    assert [row.external_item_id for row in report.top_items] == [20, 10, 30]
    assert report.top_items[1].title == "Fone novo"
    assert report.top_items[1].sales_cents == 3000
    assert report.top_items[1].orders == 2


def test_top_items_skips_rows_without_item_id(session: Session) -> None:
    order = _order(
        session,
        datetime(2026, 11, 1, 10, 0),
        sales_cents=100,
        commission_cents=10,
        title="Sem item",
    )
    order.external_item_id = None

    report = _report(session)

    assert report.top_items == []
    assert report.totals.sales_cents == 100


def test_default_period_ends_today_and_lasts_thirty_days(session: Session) -> None:
    report = DashboardService(
        session, today=lambda: date(2026, 11, 13)
    ).report("csv")

    assert report.end == date(2026, 11, 13)
    assert report.start == date(2026, 10, 15)
    assert report.days == 30
    assert report.previous_start == date(2026, 9, 15)
    assert report.previous_end == date(2026, 10, 14)


def test_source_unknown_is_rejected(session: Session) -> None:
    with pytest.raises(ValidationError) as error:
        DashboardService(session).report("todos", *NOVEMBER)

    assert error.value.details is not None
    assert error.value.details["source"] == "todos"


def test_period_with_end_before_start_is_rejected(session: Session) -> None:
    with pytest.raises(ValidationError) as error:
        DashboardService(session).report(
            "csv", date(2026, 11, 30), date(2026, 11, 1)
        )

    assert "posterior" in error.value.message


def test_period_longer_than_the_limit_is_rejected(session: Session) -> None:
    with pytest.raises(ValidationError) as error:
        DashboardService(session).report(
            "csv", date(2025, 1, 1), date(2026, 11, 1)
        )

    assert error.value.details is not None
    assert error.value.details["max_days"] == 366
