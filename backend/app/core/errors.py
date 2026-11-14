"""Erros de domínio e envelope de resposta da API.

Regra: toda falha sai no mesmo formato ``{"error": {...}}``. O frontend decide
o que mostrar a partir de ``code``; a mensagem em português é escrita aqui,
uma vez, em vez de espalhada pelos componentes.
"""

from typing import Any


class AppError(Exception):
    """Base de todas as falhas esperadas da aplicação."""

    code: str = "internal_error"
    status_code: int = 500

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class ValidationError(AppError):
    code = "validation_error"
    status_code = 422


class NotFoundError(AppError):
    code = "not_found"
    status_code = 404


class ConflictError(AppError):
    code = "conflict"
    status_code = 409


class ConfigurationError(AppError):
    """Configuração inválida que impede a operação solicitada."""

    code = "configuration_error"
    status_code = 500


class ProviderError(AppError):
    status_code = 502


class ProviderNotSupported(ProviderError):
    """Operação válida que o provedor ativo não sabe executar."""

    code = "provider_not_supported"
    status_code = 409


class ProviderAuthError(ProviderError):
    code = "provider_auth_error"


class ProviderRateLimited(ProviderError):
    code = "provider_rate_limited"
    status_code = 503

    def __init__(self, message: str, *, retry_after: int | None = None) -> None:
        super().__init__(message, details={"retry_after": retry_after})


class ProviderUnavailable(ProviderError):
    code = "provider_unavailable"
    status_code = 503


class ProviderInvalidResponse(ProviderError):
    code = "provider_invalid_response"
