"""Testes dos endpoints de sistema."""

from fastapi.testclient import TestClient

from app import __version__
from app.core.config import Settings
from app.main import create_app
from app.providers.registry import build_providers


def test_health_reports_ok(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": __version__}


def test_config_reports_demo_mode(client: TestClient) -> None:
    response = client.get("/api/config")

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "version": __version__,
        "environment": "dev",
        "provider": "demo",
        "is_demo": True,
        "capabilities": {
            "category_filter": True,
            "price_filter": True,
            "commission_filter": True,
            "sorts": [
                "relevance",
                "commission_desc",
                "sales_desc",
                "rating_desc",
                "price_asc",
                "price_desc",
            ],
        },
    }


def test_config_reports_shopee_provider_without_leaking_credentials() -> None:
    settings = Settings(
        provider="shopee",
        environment="dev",
        shopee_app_id="app-id-secreto",
        shopee_secret="segredo",
    )
    providers = build_providers(settings)
    response = TestClient(create_app(settings, providers=providers)).get("/api/config")

    assert response.status_code == 200
    body = response.json()
    assert body["is_demo"] is False
    assert body["provider"] == "shopee"
    assert body["capabilities"]["category_filter"] is False
    assert body["capabilities"]["price_filter"] is False
    assert body["capabilities"]["commission_filter"] is False
    assert "rating_desc" not in body["capabilities"]["sorts"]
    assert "app-id-secreto" not in response.text
    assert "segredo" not in response.text


def test_cors_is_enabled_only_for_dev_origins(client: TestClient) -> None:
    allowed = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    blocked = client.options(
        "/api/health",
        headers={
            "Origin": "http://evil.local",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "access-control-allow-origin" not in blocked.headers


def test_cors_is_disabled_in_prod() -> None:
    client = TestClient(create_app(Settings(environment="prod")))
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert "access-control-allow-origin" not in response.headers
