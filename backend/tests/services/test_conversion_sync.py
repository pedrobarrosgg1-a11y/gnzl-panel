"""Testes do serviço de sincronização de conversões.

O provedor é substituído por um dublê: nenhum teste toca a rede nem o banco de
desenvolvimento.
"""

from collections.abc import Sequence
from datetime import datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ProviderUnavailable, ValidationError
from app.models.conversion import Order
from app.models.import_log import ImportLog
from app.providers.base import ConversionQuery, ConversionRecord
from app.services.conversion_sync import ConversionSyncService

NOW = datetime(2026, 11, 12, 12, 0)
PURCHASE_TIME = datetime(2026, 11, 1, 10, 0)
COMPLETE_TIME = datetime(2026, 11, 2, 10, 0)


class FakeConversionProvider:
    name = "shopee"
    is_demo = False
    conversion_window_days = 90

    def __init__(
        self,
        records: Sequence[ConversionRecord] = (),
        *,
        error: Exception | None = None,
    ) -> None:
        self.records = list(records)
        self.error = error
        self.queries: list[ConversionQuery] = []

    def set_records(self, records: Sequence[ConversionRecord]) -> None:
        self.records = list(records)

    def fetch_conversions(self, query: ConversionQuery) -> list[ConversionRecord]:
        self.queries.append(query)
        if self.error is not None:
            raise self.error
        return list(self.records)


def record(
    *,
    order_id: str = "260101ABCDEF",
    item_id: int = 14888686365,
    status: str = "COMPLETED",
    status_group: str = "approved",
    commission_cents: int = 400,
    sales_cents: int = 3980,
    sub_ids: tuple[str | None, ...] = ("campanha", None, None, None, None),
    dedup_key: str = "order:abc",
) -> ConversionRecord:
    return ConversionRecord(
        external_order_id=order_id,
        external_item_id=item_id,
        shop_id=573579437,
        title="Organizador de fones",
        image_url="https://down-br.img.susercontent.com/file/abc",
        status=status,
        status_group=status_group,
        ordered_at=PURCHASE_TIME,
        completed_at=COMPLETE_TIME,
        quantity=2,
        sales_cents=sales_cents,
        commission_cents=commission_cents,
        sub_ids=sub_ids,
        channel="APP",
        dedup_key=dedup_key,
        source="shopee",
        raw={"order_id": order_id, "item": {"itemId": item_id}},
    )


def service(
    session: Session, provider: FakeConversionProvider
) -> ConversionSyncService:
    return ConversionSyncService(session, provider, now=lambda: NOW)


def orders(session: Session) -> list[Order]:
    return list(session.scalars(select(Order).order_by(Order.id)).all())


def logs(session: Session) -> list[ImportLog]:
    return list(session.scalars(select(ImportLog).order_by(ImportLog.id)).all())


def test_sync_creates_orders_and_a_completed_import_log(session: Session) -> None:
    provider = FakeConversionProvider([record()])

    result = service(session, provider).sync(days=30)

    assert result.total == 1
    assert result.created == 1
    assert result.updated == 0
    assert result.skipped == 0
    assert result.failed == 0
    assert result.window_start == NOW - timedelta(days=30)
    assert result.window_end == NOW
    assert provider.queries == [ConversionQuery(NOW - timedelta(days=30), NOW)]

    [order] = orders(session)
    assert order.data_source == "shopee"
    assert order.external_order_id == "260101ABCDEF"
    assert order.dedup_key == "order:abc"
    assert order.sales_cents == 3980
    assert order.commission_cents == 400
    assert order.status_group == "approved"
    assert order.sub_id_1 == "campanha"
    assert order.sub_id_2 is None
    assert order.channel == "APP"
    assert order.import_id == result.log.id

    [log] = logs(session)
    assert log.status == "completed"
    assert log.report_type == "orders"
    assert log.data_source == "shopee"
    assert log.filename == "shopee:conversion-report:2026-10-13:2026-11-12"
    assert log.rows_total == 1
    assert log.rows_imported == 1
    assert log.rows_skipped == 0
    assert log.rows_failed == 0
    assert log.finished_at is not None
    assert len(log.rows) == 1
    assert log.rows[0].status == "imported"
    assert log.rows[0].order_id == order.id
    assert "260101ABCDEF" in (log.rows[0].raw_data or "")


def test_sync_is_idempotent_when_nothing_changed(session: Session) -> None:
    provider = FakeConversionProvider([record()])
    service(session, provider).sync(days=30)

    second = service(session, provider).sync(days=30)

    assert second.created == 0
    assert second.updated == 0
    assert second.skipped == 1
    assert len(orders(session)) == 1
    assert len(logs(session)) == 2
    assert second.log.rows_imported == 0
    assert second.log.rows_skipped == 1
    assert second.log.rows[0].message == "Pedido já sincronizado; nada mudou."


def test_sync_updates_status_and_commission_of_an_existing_order(
    session: Session,
) -> None:
    provider = FakeConversionProvider([record()])
    service(session, provider).sync(days=30)
    provider.set_records(
        [
            record(
                status="CANCELLED",
                status_group="cancelled",
                commission_cents=0,
            )
        ]
    )

    second = service(session, provider).sync(days=30)

    assert second.created == 0
    assert second.updated == 1
    assert second.skipped == 0
    [order] = orders(session)
    assert order.status == "CANCELLED"
    assert order.status_group == "cancelled"
    assert order.commission_cents == 0
    assert second.log.rows_imported == 1
    assert second.log.rows[0].status == "imported"
    assert "atualizado" in (second.log.rows[0].message or "")


def test_sync_skips_rows_repeated_inside_the_same_run(session: Session) -> None:
    provider = FakeConversionProvider([record(), record(item_id=999)])

    result = service(session, provider).sync(days=30)

    assert result.created == 1
    assert result.skipped == 1
    assert len(orders(session)) == 1
    assert result.log.rows[1].status == "skipped"
    assert "mesma sincronização" in (result.log.rows[1].message or "")


def test_sync_keeps_sources_separate_even_with_the_same_dedup_key(
    session: Session,
) -> None:
    session.add(
        Order(
            external_order_id="csv-1",
            status="Aprovado",
            status_group="approved",
            ordered_at=PURCHASE_TIME,
            quantity=1,
            sales_cents=100,
            commission_cents=10,
            data_source="csv",
            dedup_key="order:abc",
        )
    )
    session.commit()
    provider = FakeConversionProvider([record()])

    result = service(session, provider).sync(days=30)

    assert result.created == 1
    assert len(orders(session)) == 2
    assert {order.data_source for order in orders(session)} == {"csv", "shopee"}


def test_sync_without_conversions_records_an_empty_run(session: Session) -> None:
    result = service(session, FakeConversionProvider([])).sync(days=7)

    assert result.total == 0
    assert result.created == 0
    assert orders(session) == []
    [log] = logs(session)
    assert log.status == "completed"
    assert log.rows_total == 0
    assert log.rows == []


def test_provider_failure_writes_nothing(session: Session) -> None:
    provider = FakeConversionProvider(error=ProviderUnavailable("fora do ar"))

    with pytest.raises(ProviderUnavailable):
        service(session, provider).sync(days=30)

    assert orders(session) == []
    assert logs(session) == []


@pytest.mark.parametrize("days", [0, -1, 91])
def test_window_outside_the_provider_limit_is_rejected_before_calling(
    session: Session, days: int
) -> None:
    provider = FakeConversionProvider([record()])

    with pytest.raises(ValidationError) as error:
        service(session, provider).sync(days=days)

    assert error.value.details == {"days": days, "max_days": 90}
    assert provider.queries == []
    assert logs(session) == []
