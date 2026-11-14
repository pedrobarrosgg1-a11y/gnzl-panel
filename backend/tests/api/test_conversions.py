"""Testes do endpoint de sincronização de conversões.

O provedor de conversões é um dublê: nenhum teste toca a rede da Shopee.
"""

from collections.abc import Iterator, Sequence
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from app.core.config import Settings
from app.core.errors import ProviderUnavailable
from app.main import create_app
from app.providers.base import ConversionQuery, ConversionRecord
from app.providers.capabilities import SHOPEE_CAPABILITIES
from app.providers.demo import DemoProvider
from app.providers.registry import Providers

PURCHASE_TIME = datetime(2026, 11, 1, 10, 0)


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

    def fetch_conversions(self, query: ConversionQuery) -> list[ConversionRecord]:
        if self.error is not None:
            raise self.error
        return list(self.records)


def record() -> ConversionRecord:
    return ConversionRecord(
        external_order_id="260101ABCDEF",
        external_item_id=14888686365,
        shop_id=573579437,
        title="Organizador de fones",
        image_url="https://down-br.img.susercontent.com/file/abc",
        status="COMPLETED",
        status_group="approved",
        ordered_at=PURCHASE_TIME,
        completed_at=None,
        quantity=2,
        sales_cents=3980,
        commission_cents=400,
        sub_ids=("campanha", None, None, None, None),
        channel="APP",
        dedup_key="order:abc",
        source="shopee",
        raw={"order_id": "260101ABCDEF", "item": {"itemId": 14888686365}},
    )


@pytest.fixture
def shopee_client(
    engine: Engine,
) -> Iterator[tuple[TestClient, FakeConversionProvider]]:
    provider = FakeConversionProvider([record()])
    demo = DemoProvider()
    providers = Providers(
        product=demo,
        link=demo,
        source="shopee",
        capabilities=SHOPEE_CAPABILITIES,
        conversions=provider,
    )
    settings = Settings(
        provider="shopee",
        environment="dev",
        shopee_app_id="app-id-de-teste",
        shopee_secret="segredo-de-teste",
    )
    with TestClient(
        create_app(settings, providers=providers, engine=engine)
    ) as client:
        yield client, provider


def test_demo_mode_refuses_conversion_sync(client: TestClient) -> None:
    response = client.post("/api/conversions/sync")

    assert response.status_code == 409
    error = response.json()["error"]
    assert error["code"] == "provider_not_supported"
    assert "GNZL_PROVIDER=shopee" in error["message"]


def test_sync_creates_orders_and_appears_in_the_import_history(
    shopee_client: tuple[TestClient, FakeConversionProvider],
) -> None:
    client, _ = shopee_client

    response = client.post("/api/conversions/sync", params={"days": 30})

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["total"] == 1
    assert body["created"] == 1
    assert body["updated"] == 0
    assert body["skipped"] == 0
    assert body["failed"] == 0
    assert body["window_end"].endswith("Z")
    start = datetime.fromisoformat(body["window_start"].replace("Z", "+00:00"))
    end = datetime.fromisoformat(body["window_end"].replace("Z", "+00:00"))
    assert end - start == timedelta(days=30)

    log = body["import_log"]
    assert log["report_type"] == "orders"
    assert log["status"] == "completed"
    assert log["source"] == "shopee"
    assert log["is_demo"] is False
    assert log["rows_imported"] == 1
    assert log["filename"].startswith("shopee:conversion-report:")

    history = client.get("/api/imports").json()
    assert history["total"] == 1
    assert history["items"][0]["id"] == log["id"]

    detail = client.get(f"/api/imports/{log['id']}").json()
    assert detail["rows_matching"] == 1
    row = detail["rows"][0]
    assert row["status"] == "imported"
    assert row["order_id"] is not None
    assert row["raw_data"]["order_id"] == "260101ABCDEF"


def test_sync_twice_keeps_the_history_and_skips_unchanged_rows(
    shopee_client: tuple[TestClient, FakeConversionProvider],
) -> None:
    client, _ = shopee_client

    client.post("/api/conversions/sync", params={"days": 30})
    second = client.post("/api/conversions/sync", params={"days": 30})

    assert second.status_code == 201
    body = second.json()
    assert body["created"] == 0
    assert body["updated"] == 0
    assert body["skipped"] == 1
    assert body["import_log"]["rows_imported"] == 0
    assert body["import_log"]["rows_skipped"] == 1
    assert client.get("/api/imports").json()["total"] == 2


@pytest.mark.parametrize("days", [0, 91])
def test_days_outside_the_window_is_rejected(
    shopee_client: tuple[TestClient, FakeConversionProvider], days: int
) -> None:
    client, _ = shopee_client

    response = client.post("/api/conversions/sync", params={"days": days})

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert any("days" in field["field"] for field in error["details"]["fields"])
    assert client.get("/api/imports").json()["total"] == 0


def test_provider_failure_keeps_the_standard_error_envelope_and_writes_nothing(
    shopee_client: tuple[TestClient, FakeConversionProvider],
) -> None:
    client, provider = shopee_client
    provider.error = ProviderUnavailable("A Shopee está indisponível.")

    response = client.post("/api/conversions/sync")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "provider_unavailable"
    assert client.get("/api/imports").json()["total"] == 0
