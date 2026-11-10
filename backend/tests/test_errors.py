"""Testes do envelope de erro da API."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.errors import register_error_handlers
from app.core.errors import ProviderRateLimited


def _app_with_error(error: Exception) -> FastAPI:
    app = FastAPI()

    @app.middleware("http")
    async def attach_request_id(request, call_next):
        request.state.request_id = "req-de-teste"
        return await call_next(request)

    register_error_handlers(app)

    @app.get("/falha")
    def fail() -> None:
        raise error

    return app


def test_domain_error_uses_the_standard_envelope() -> None:
    response = TestClient(
        _app_with_error(ProviderRateLimited("Limite atingido.", retry_after=30)),
        raise_server_exceptions=False,
    ).get("/falha")

    assert response.status_code == 503
    body = response.json()
    assert body["error"]["code"] == "provider_rate_limited"
    assert body["error"]["message"] == "Limite atingido."
    assert body["error"]["details"] == {"retry_after": 30}
    assert body["error"]["request_id"] == "req-de-teste"


def test_unexpected_error_hides_internals() -> None:
    response = TestClient(
        _app_with_error(RuntimeError("senha do banco: 123")),
        raise_server_exceptions=False,
    ).get("/falha")

    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "internal_error"
    assert "senha" not in response.text


def test_validation_error_is_translated() -> None:
    client = TestClient(_app_with_error(RuntimeError("não usado")))

    response = client.get("/nao-existe")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
