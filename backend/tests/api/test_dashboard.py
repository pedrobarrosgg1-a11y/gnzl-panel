"""Testes do endpoint do dashboard."""

from datetime import date

from fastapi.testclient import TestClient

from app.core.time import local_today

ORDER_HEADER = (
    "order_id,item_id,shop_id,status,status_group,ordered_at,quantity,"
    "sales_cents,commission_cents,sub_id_1,channel,title,image_url,completed_at"
)

CLICK_HEADER = "click_id,clicked_at,region,channel,referrer,sub_id_1,sub_id_2"


def _csv(header: str, *rows: str) -> bytes:
    return ("\n".join([header, *rows]) + "\n").encode("utf-8")


def _post_orders(client: TestClient, *rows: str) -> None:
    response = client.post(
        "/api/imports/orders",
        params={"filename": "conversion.csv"},
        content=_csv(ORDER_HEADER, *rows),
        headers={"Content-Type": "text/csv"},
    )
    assert response.status_code == 201, response.text


def _post_clicks(client: TestClient, *rows: str) -> None:
    response = client.post(
        "/api/imports/clicks",
        params={"filename": "clicks.csv"},
        content=_csv(CLICK_HEADER, *rows),
        headers={"Content-Type": "text/csv"},
    )
    assert response.status_code == 201, response.text


def _order_row(order_id: str, item_id: str, *, ordered_at: str) -> str:
    return (
        f"{order_id},{item_id},100,Aprovado,,{ordered_at},2,19990,1700,"
        f"instagram,app,Fone bluetooth,https://img.example/x.jpg,"
    )


def test_dashboard_aggregates_the_csv_source(client: TestClient) -> None:
    _post_orders(
        client,
        _order_row("A1", "10", ordered_at="2026-11-05T10:00:00"),
        _order_row("A2", "10", ordered_at="2026-11-06T10:00:00"),
    )
    _post_clicks(
        client,
        "c-1,2026-11-05T10:00:00,BR,app,https://ref,instagram,",
        "c-2,2026-11-06T10:00:00,BR,app,https://ref,instagram,",
    )

    response = client.get(
        "/api/dashboard",
        params={
            "source": "csv",
            "start": "2026-11-01",
            "end": "2026-11-30",
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["source"] == "csv"
    assert body["is_demo"] is False
    assert body["start"] == "2026-11-01"
    assert body["end"] == "2026-11-30"
    assert body["days"] == 30
    assert body["previous_start"] == "2026-10-02"
    assert body["previous_end"] == "2026-10-31"

    metrics = body["metrics"]
    assert metrics["sales_cents"] == 39980
    assert metrics["commission_cents"] == 3400
    assert metrics["orders"] == 2
    assert metrics["clicks"] == 2
    assert metrics["conversion_bp"] == 10000
    assert metrics["average_ticket_cents"] == 19990

    assert body["comparisons"]["sales_cents"] == {
        "previous": 0,
        "absolute": 39980,
        "variation_bp": None,
    }
    assert len(body["daily"]) == 30
    assert body["daily"][4] == {
        "date": "2026-11-05",
        "sales_cents": 19990,
        "commission_cents": 1700,
        "orders": 1,
        "clicks": 1,
    }
    assert body["top_sub_ids"] == [
        {
            "sub_id_1": "instagram",
            "sales_cents": 39980,
            "commission_cents": 3400,
            "orders": 2,
            "clicks": 2,
        }
    ]
    assert body["top_items"] == [
        {
            "external_item_id": 10,
            "title": "Fone bluetooth",
            "sales_cents": 39980,
            "commission_cents": 3400,
            "orders": 2,
        }
    ]


def test_dashboard_default_period_ends_today(client: TestClient) -> None:
    response = client.get("/api/dashboard", params={"source": "csv"})

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["end"] == local_today().isoformat()
    assert body["days"] == 30
    start = date.fromisoformat(body["start"])
    end = date.fromisoformat(body["end"])
    assert (end - start).days == 29


def test_dashboard_keeps_sources_separate(client: TestClient) -> None:
    _post_orders(client, _order_row("A1", "10", ordered_at="2026-11-05T10:00:00"))

    response = client.get(
        "/api/dashboard",
        params={
            "source": "shopee",
            "start": "2026-11-01",
            "end": "2026-11-30",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["metrics"]["sales_cents"] == 0
    assert body["metrics"]["orders"] == 0
    assert body["top_items"] == []


def test_dashboard_demo_source_is_flagged(client: TestClient) -> None:
    response = client.get("/api/dashboard", params={"source": "demo"})

    assert response.status_code == 200
    assert response.json()["is_demo"] is True


def test_source_is_required(client: TestClient) -> None:
    response = client.get("/api/dashboard")

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert any("source" in field["field"] for field in error["details"]["fields"])


def test_unknown_source_is_rejected(client: TestClient) -> None:
    response = client.get("/api/dashboard", params={"source": "todos"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_start_after_end_is_rejected_with_the_standard_envelope(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/dashboard",
        params={
            "source": "csv",
            "start": "2026-11-30",
            "end": "2026-11-01",
        },
    )

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert "posterior" in error["message"]


def test_period_longer_than_the_limit_is_rejected(client: TestClient) -> None:
    response = client.get(
        "/api/dashboard",
        params={
            "source": "csv",
            "start": "2025-01-01",
            "end": "2026-11-01",
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["details"]["max_days"] == 366
