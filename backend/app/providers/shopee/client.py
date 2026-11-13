"""Cliente GraphQL da Open API de afiliados da Shopee.

Pontos que a documentação não oficial erra ou omite e que este módulo trata:

- a assinatura cobre os bytes JSON exatos enviados, por isso o corpo é
  serializado em UTF-8 compacto (``ensure_ascii=False``) antes de assinar;
- ``generateShortLink`` recebe ``input: ShortLinkInput``, não argumentos soltos;
- o código ``10000`` aparece de forma intermitente, mesmo em chamadas idênticas
  e com parâmetros válidos, com falhas rápidas e taxa de sucesso próxima de
  metade. Por isso as consultas usam oito tentativas com backoff curto; o
  limite de rate limit continua em três, para não insistir quando a Shopee
  pede para desacelerar. Mutations nunca são repetidas automaticamente, porque
  uma resposta perdida pode significar que o link já foi criado.
"""

from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable
from typing import Any

import httpx

from app.core.errors import (
    AppError,
    ProviderAuthError,
    ProviderInvalidResponse,
    ProviderRateLimited,
    ProviderUnavailable,
)

# Códigos de erro documentados pela Shopee.
CODE_AUTH = 10020
CODE_RATE_LIMITED = 10030
CODE_NOT_AUTHORIZED = 10035
CODE_SYSTEM = 10000
CODE_INVALID_PARAMETERS = 11001


class ShopeeClient:
    """Executa consultas GraphQL assinadas contra a Open API da Shopee."""

    def __init__(
        self,
        *,
        app_id: str,
        secret: str,
        api_base: str,
        timeout: float,
        transport: httpx.BaseTransport | None = None,
        max_attempts: int = 8,
        max_rate_limit_attempts: int = 3,
        retry_base_delay: float = 0.5,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._app_id = app_id
        self._secret = secret
        self._api_base = api_base
        self._timeout = timeout
        self._transport = transport
        self._max_attempts = max(1, max_attempts)
        self._max_rate_limit_attempts = max(1, max_rate_limit_attempts)
        self._retry_base_delay = retry_base_delay
        self._sleep = sleep

    def execute(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
        *,
        retry: bool = True,
    ) -> dict[str, Any]:
        """Executa a query e devolve o objeto ``data`` já validado.

        ``retry=False`` é obrigatório para mutations. O chamador não deve
        repetir uma operação que pode gerar efeito duplicado.
        """
        body = self._encode(query, variables)
        attempts = self._max_attempts if retry else 1
        rate_limit_failures = 0
        last_error: AppError | None = None

        for attempt in range(attempts):
            if attempt > 0:
                self._sleep(self._backoff(attempt))

            try:
                response = self._post(body)
            except httpx.TimeoutException:
                last_error = ProviderUnavailable(
                    "A Shopee não respondeu dentro do tempo esperado."
                )
                continue
            except httpx.TransportError:
                last_error = ProviderUnavailable(
                    "Não foi possível conectar à Shopee."
                )
                continue

            if response.status_code in (401, 403):
                raise ProviderAuthError(
                    "A Shopee recusou a autenticação da integração."
                )
            if response.status_code == 429:
                rate_limit_failures += 1
                last_error = ProviderRateLimited(
                    "A Shopee limitou a taxa de requisições.",
                    retry_after=_retry_after(response),
                )
                if not retry or rate_limit_failures >= self._max_rate_limit_attempts:
                    break
                continue
            if response.status_code >= 500:
                last_error = ProviderUnavailable(
                    "A Shopee respondeu com um erro interno."
                )
                continue
            if response.status_code >= 400:
                raise ProviderInvalidResponse(
                    f"A Shopee rejeitou a requisição (HTTP {response.status_code})."
                )

            payload = self._decode(response)
            errors = payload.get("errors")
            if errors:
                error = self._error_from(errors)
                if isinstance(error, ProviderRateLimited):
                    rate_limit_failures += 1
                    if (
                        not retry
                        or rate_limit_failures >= self._max_rate_limit_attempts
                    ):
                        raise error
                    last_error = error
                    continue
                if isinstance(error, ProviderUnavailable):
                    if not retry:
                        raise error
                    last_error = error
                    continue
                raise error

            data = payload.get("data")
            if not isinstance(data, dict):
                raise ProviderInvalidResponse(
                    "A Shopee devolveu uma resposta sem dados."
                )
            return data

        assert last_error is not None
        raise last_error

    def _post(self, body: bytes) -> httpx.Response:
        timestamp = str(int(time.time()))
        headers = {
            "Content-Type": "application/json",
            "Authorization": self._authorization(timestamp, body),
        }
        with httpx.Client(
            transport=self._transport, timeout=self._timeout
        ) as client:
            return client.post(self._api_base, content=body, headers=headers)

    def _authorization(self, timestamp: str, body: bytes) -> str:
        signature = hashlib.sha256(
            self._app_id.encode()
            + timestamp.encode()
            + body
            + self._secret.encode()
        ).hexdigest()
        return (
            f"SHA256 Credential={self._app_id}, "
            f"Timestamp={timestamp}, Signature={signature}"
        )

    @staticmethod
    def _encode(query: str, variables: dict[str, Any] | None) -> bytes:
        payload: dict[str, Any] = {"query": query}
        if variables is not None:
            payload["variables"] = variables
        return json.dumps(
            payload, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")

    @staticmethod
    def _decode(response: httpx.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError as exc:
            raise ProviderInvalidResponse(
                "A Shopee devolveu uma resposta que não é JSON."
            ) from exc
        if not isinstance(payload, dict):
            raise ProviderInvalidResponse(
                "A Shopee devolveu uma resposta em formato inesperado."
            )
        return payload

    @staticmethod
    def _error_from(errors: Any) -> AppError:
        codes = []
        for item in errors if isinstance(errors, list) else [errors]:
            if not isinstance(item, dict):
                continue
            extensions = item.get("extensions")
            code = extensions.get("code") if isinstance(extensions, dict) else None
            try:
                codes.append(int(code))
            except (TypeError, ValueError):
                continue

        if CODE_AUTH in codes or CODE_NOT_AUTHORIZED in codes:
            message = (
                "A conta da Shopee não tem acesso à Open API."
                if CODE_NOT_AUTHORIZED in codes
                else "A Shopee recusou as credenciais configuradas."
            )
            return ProviderAuthError(message)
        if CODE_RATE_LIMITED in codes:
            return ProviderRateLimited(
                "A Shopee limitou a taxa de requisições."
            )
        if CODE_SYSTEM in codes:
            return ProviderUnavailable(
                "A Shopee retornou um erro interno temporário."
            )
        if CODE_INVALID_PARAMETERS in codes:
            return ProviderInvalidResponse(
                "A Shopee rejeitou os parâmetros da requisição."
            )
        code = codes[0] if codes else "desconhecido"
        return ProviderInvalidResponse(
            f"A Shopee retornou um erro não esperado ({code})."
        )

    def _backoff(self, attempt: int) -> float:
        # Falhas 10000 retornam rápido; não vale esperar 8 s entre tentativas.
        return min(self._retry_base_delay * (2 ** (attempt - 1)), 2.0)


def _retry_after(response: httpx.Response) -> int | None:
    value = response.headers.get("Retry-After")
    if not value:
        return None
    try:
        return max(0, int(value))
    except ValueError:
        return None
