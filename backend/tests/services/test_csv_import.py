"""Testes do parser e do serviço de importação CSV."""

import json
from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from app.core.errors import ValidationError
from app.models.conversion import Click, Order
from app.models.import_log import ImportedRow, ImportLog
from app.services.csv_import import CsvImportService

ORDER_HEADER = (
    "order_id,item_id,shop_id,status,status_group,ordered_at,quantity,"
    "sales_cents,commission_cents,sub_id_1,channel,title,image_url,completed_at"
)

CLICK_HEADER = "click_id,clicked_at,region,channel,referrer,sub_id_1,sub_id_2"


def _csv(header: str, *rows: str, encoding: str = "utf-8") -> bytes:
    text = "\n".join([header, *rows]) + "\n"
    return text.encode(encoding)


def _order_row(
    order_id: str = "A1",
    item_id: str = "10",
    *,
    status_group: str = "approved",
    ordered_at: str = "2026-11-01T10:00:00",
    quantity: str = "2",
    sales_cents: str = "19990",
    commission_cents: str = "1700",
    sub_id_1: str = "Instagram",
) -> str:
    return ",".join(
        [
            order_id,
            item_id,
            "100",
            "Aprovado",
            status_group,
            ordered_at,
            quantity,
            sales_cents,
            commission_cents,
            sub_id_1,
            "instagram",
            "Fone bluetooth",
            "https://img.example/x.jpg",
            "2026-11-02T10:00:00",
        ]
    )


def test_import_orders_records_order_rows_and_counters(session: Session) -> None:
    service = CsvImportService(session)

    log = service.import_orders(
        "conversion.csv", _csv(ORDER_HEADER, _order_row())
    )

    assert log.report_type == "orders"
    assert log.data_source == "csv"
    assert log.status == "completed"
    assert log.rows_total == 1
    assert log.rows_imported == 1
    assert log.rows_skipped == 0
    assert log.rows_failed == 0
    assert log.finished_at is not None

    order = session.query(Order).one()
    assert order.external_order_id == "A1"
    assert order.external_item_id == 10
    assert order.shop_id == 100
    assert order.status == "Aprovado"
    assert order.status_group == "approved"
    assert order.quantity == 2
    assert order.sales_cents == 19990
    assert order.commission_cents == 1700
    assert order.sub_id_1 == "instagram"
    assert order.data_source == "csv"
    assert order.import_id == log.id

    row = session.query(ImportedRow).one()
    assert row.status == "imported"
    assert row.order_id == order.id
    assert row.click_id is None
    assert json.loads(row.raw_data or "{}")["order_id"] == "A1"


def test_reimporting_the_same_file_skips_instead_of_duplicating(
    session: Session,
) -> None:
    service = CsvImportService(session)
    content = _csv(ORDER_HEADER, _order_row())

    service.import_orders("conversion.csv", content)
    second = service.import_orders("conversion.csv", content)

    assert second.rows_total == 1
    assert second.rows_imported == 0
    assert second.rows_skipped == 1
    assert second.status == "completed"
    assert session.query(Order).count() == 1
    assert session.query(ImportLog).count() == 2

    row = session.query(ImportedRow).filter_by(import_id=second.id).one()
    order = session.query(Order).one()
    assert row.status == "skipped"
    assert row.order_id == order.id


def test_duplicate_rows_inside_the_same_file_are_skipped(session: Session) -> None:
    service = CsvImportService(session)

    log = service.import_orders(
        "conversion.csv",
        _csv(ORDER_HEADER, _order_row(), _order_row()),
    )

    assert log.rows_total == 2
    assert log.rows_imported == 1
    assert log.rows_skipped == 1
    assert session.query(Order).count() == 1


def test_invalid_rows_do_not_abort_the_import(session: Session) -> None:
    service = CsvImportService(session)
    content = _csv(
        ORDER_HEADER,
        _order_row("A1", "10"),
        _order_row("A2", "11", ordered_at="32/13/2026 10:00"),
        _order_row("A3", "12", sales_cents="abc"),
        _order_row("A4", "13", status_group="aprovado"),
    )

    log = service.import_orders("conversion.csv", content)

    assert log.rows_total == 4
    assert log.rows_imported == 1
    assert log.rows_failed == 3
    assert log.status == "partial"
    assert session.query(Order).count() == 1

    errors = (
        session.query(ImportedRow).filter_by(status="error").order_by(
            ImportedRow.row_number
        )
    ).all()
    assert [error.row_number for error in errors] == [3, 4, 5]
    assert "ordered_at" in errors[0].message
    assert "sales_cents" in errors[1].message
    assert "status_group" in errors[2].message
    assert errors[0].raw_data is not None


def test_import_with_only_errors_is_marked_failed(session: Session) -> None:
    service = CsvImportService(session)
    content = _csv(ORDER_HEADER, _order_row("A1", "10", sales_cents="abc"))

    log = service.import_orders("conversion.csv", content)

    assert log.status == "failed"
    assert log.rows_imported == 0
    assert log.rows_failed == 1


def test_missing_required_column_is_rejected_before_writing(
    session: Session,
) -> None:
    header = "order_id,item_id,status,sales_cents"

    with pytest.raises(ValidationError) as captured:
        CsvImportService(session).import_orders(
            "conversion.csv", _csv(header, "A1,10,Aprovado,0")
        )

    assert captured.value.details is not None
    assert captured.value.details["missing_columns"] == ["ordered_at"]
    assert session.query(ImportLog).count() == 0
    assert session.query(Order).count() == 0


def test_empty_file_is_rejected(session: Session) -> None:
    with pytest.raises(ValidationError):
        CsvImportService(session).import_orders("conversion.csv", b"")


def test_header_without_rows_is_rejected(session: Session) -> None:
    with pytest.raises(ValidationError):
        CsvImportService(session).import_orders(
            "conversion.csv", _csv(ORDER_HEADER)
        )


def test_semicolon_bom_and_brazilian_date_are_accepted(session: Session) -> None:
    content = (
        "\ufeff"
        + ORDER_HEADER.replace(",", ";")
        + "\r\n"
        + _order_row(ordered_at="01/11/2026 10:30").replace(",", ";")
        + "\r\n"
    ).encode("utf-8")

    log = CsvImportService(session).import_orders("conversion.csv", content)

    assert log.rows_imported == 1
    order = session.query(Order).one()
    assert order.ordered_at == datetime(2026, 11, 1, 10, 30)


def test_windows_1252_file_is_accepted(session: Session) -> None:
    content = _csv(ORDER_HEADER, _order_row(), encoding="cp1252").replace(
        b"Fone bluetooth", "Fone bluetooth ação".encode("cp1252")
    )

    log = CsvImportService(session).import_orders("conversion.csv", content)

    assert log.rows_imported == 1
    assert session.query(Order).one().title == "Fone bluetooth ação"


def test_optional_columns_use_safe_defaults(session: Session) -> None:
    content = _csv(ORDER_HEADER, "A9,19,100,Aprovado,approved,2026-11-01T10:00:00")

    log = CsvImportService(session).import_orders("conversion.csv", content)

    assert log.rows_imported == 1
    order = session.query(Order).one()
    assert order.quantity == 1
    assert order.sales_cents == 0
    assert order.commission_cents == 0
    assert order.status_group == "approved"
    assert order.sub_id_1 is None
    assert order.title is None


def test_missing_status_group_defaults_to_unknown(session: Session) -> None:
    content = _csv(
        ORDER_HEADER,
        "A9,19,100,Aprovado,,2026-11-01T10:00:00",
    )

    CsvImportService(session).import_orders("conversion.csv", content)

    assert session.query(Order).one().status_group == "unknown"


def test_import_clicks_converts_timezone_and_links_rows(session: Session) -> None:
    content = _csv(
        CLICK_HEADER,
        "c-1,2026-11-01T10:00:00-03:00,BR,Instagram,https://ref,Stories,Feed",
    )

    log = CsvImportService(session).import_clicks("clicks.csv", content)

    assert log.report_type == "clicks"
    assert log.status == "completed"
    click = session.query(Click).one()
    assert click.external_click_id == "c-1"
    assert click.clicked_at == datetime(2026, 11, 1, 13, 0)
    assert click.region == "BR"
    assert click.channel == "Instagram"
    assert click.sub_id_1 == "stories"
    assert click.sub_id_2 == "feed"
    assert click.import_id == log.id

    row = session.query(ImportedRow).one()
    assert row.click_id == click.id
    assert row.order_id is None


def test_reimporting_clicks_is_idempotent(session: Session) -> None:
    content = _csv(CLICK_HEADER, "c-1,2026-11-01T10:00:00")
    service = CsvImportService(session)

    service.import_clicks("clicks.csv", content)
    second = service.import_clicks("clicks.csv", content)

    assert second.rows_skipped == 1
    assert session.query(Click).count() == 1
