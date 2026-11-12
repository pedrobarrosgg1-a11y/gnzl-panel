"""Testes dos endpoints de importação CSV."""

from fastapi.testclient import TestClient

ORDER_HEADER = (
    "order_id,item_id,shop_id,status,status_group,ordered_at,quantity,"
    "sales_cents,commission_cents,sub_id_1,channel,title,image_url,completed_at"
)

CLICK_HEADER = "click_id,clicked_at,region,channel,referrer,sub_id_1,sub_id_2"


def _post_orders(
    client: TestClient,
    content: bytes,
    *,
    filename: str = "conversion.csv",
):
    return client.post(
        "/api/imports/orders",
        params={"filename": filename},
        content=content,
        headers={"Content-Type": "text/csv"},
    )


def _csv(header: str, *rows: str) -> bytes:
    return ("\n".join([header, *rows]) + "\n").encode("utf-8")


def _order_row(order_id: str = "A1", item_id: str = "10") -> str:
    return (
        f"{order_id},{item_id},100,Aprovado,approved,2026-11-01T10:00:00,"
        "2,19990,1700,instagram,instagram,Fone bluetooth,,"
    )


def test_import_orders_returns_summary_and_is_visible_in_history(
    client: TestClient,
) -> None:
    response = _post_orders(client, _csv(ORDER_HEADER, _order_row()))

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["filename"] == "conversion.csv"
    assert body["report_type"] == "orders"
    assert body["status"] == "completed"
    assert body["source"] == "csv"
    assert body["is_demo"] is False
    assert body["rows_total"] == 1
    assert body["rows_imported"] == 1
    assert body["rows_skipped"] == 0
    assert body["rows_failed"] == 0
    assert body["finished_at"] is not None

    listing = client.get("/api/imports").json()
    assert listing["total"] == 1
    assert listing["items"][0]["id"] == body["id"]

    detail = client.get(f"/api/imports/{body['id']}").json()
    assert detail["rows_matching"] == 1
    row = detail["rows"][0]
    assert row["status"] == "imported"
    assert row["order_id"] is not None
    assert row["click_id"] is None
    assert row["raw_data"]["order_id"] == "A1"


def test_reimport_through_api_skips_existing_rows(client: TestClient) -> None:
    content = _csv(ORDER_HEADER, _order_row())

    _post_orders(client, content)
    second = _post_orders(client, content)

    assert second.status_code == 201
    body = second.json()
    assert body["rows_imported"] == 0
    assert body["rows_skipped"] == 1
    assert body["status"] == "completed"
    assert client.get("/api/imports").json()["total"] == 2


def test_invalid_csv_returns_validation_error(client: TestClient) -> None:
    response = _post_orders(
        client,
        _csv("order_id,item_id,status", "A1,10,Aprovado"),
    )

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert "ordered_at" in error["details"]["missing_columns"]
    assert client.get("/api/imports").json()["total"] == 0


def test_unknown_import_returns_not_found(client: TestClient) -> None:
    response = client.get("/api/imports/999")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_detail_filters_rows_and_paginates(client: TestClient) -> None:
    content = _csv(
        ORDER_HEADER,
        _order_row("A1", "10"),
        _order_row("A2", "11").replace(",2,19990,1700,", ",2,abc,1700,"),
    )
    import_id = _post_orders(client, content).json()["id"]

    errors = client.get(
        f"/api/imports/{import_id}", params={"row_status": "error"}
    ).json()
    assert errors["rows_matching"] == 1
    assert errors["rows"][0]["status"] == "error"
    assert "sales_cents" in errors["rows"][0]["message"]

    first_page = client.get(
        f"/api/imports/{import_id}", params={"page_size": 1}
    ).json()
    assert len(first_page["rows"]) == 1
    assert first_page["rows_matching"] == 2
    assert first_page["rows_has_next"] is True

    second_page = client.get(
        f"/api/imports/{import_id}", params={"page_size": 1, "page": 2}
    ).json()
    assert len(second_page["rows"]) == 1
    assert second_page["rows_has_next"] is False


def test_filename_is_reduced_to_a_safe_name(client: TestClient) -> None:
    response = _post_orders(
        client,
        _csv(ORDER_HEADER, _order_row()),
        filename="..\\..\\relatorio-real.csv",
    )

    assert response.status_code == 201
    assert response.json()["filename"] == "relatorio-real.csv"


def test_import_clicks_endpoint(client: TestClient) -> None:
    response = client.post(
        "/api/imports/clicks",
        params={"filename": "clicks.csv"},
        content=_csv(
            CLICK_HEADER,
            "c-1,2026-11-01T10:00:00-03:00,BR,Instagram,https://ref,stories,feed",
        ),
        headers={"Content-Type": "text/csv"},
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["report_type"] == "clicks"
    assert body["rows_imported"] == 1

    detail = client.get(f"/api/imports/{body['id']}").json()
    row = detail["rows"][0]
    assert row["click_id"] is not None
    assert row["order_id"] is None
