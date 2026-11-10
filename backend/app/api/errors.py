"""Handlers que garantem um único formato de erro para toda a API."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.errors import AppError

logger = logging.getLogger(__name__)

_HTTP_CODES = {
    404: ("not_found", "Recurso não encontrado."),
    405: ("method_not_allowed", "Método não permitido para este recurso."),
}


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def _payload(
    code: str,
    message: str,
    request: Request,
    details: dict | None = None,
) -> dict:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "request_id": _request_id(request),
        }
    }


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        if exc.status_code >= 500:
            logger.warning("%s: %s", exc.code, exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content=_payload(exc.code, exc.message, request, exc.details),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        code, message = _HTTP_CODES.get(
            exc.status_code, ("http_error", "Não foi possível atender a requisição.")
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=_payload(code, message, request, exc.detail if exc.detail else None),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        fields = [
            {"field": ".".join(str(part) for part in error["loc"]), "message": error["msg"]}
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=_payload(
                "validation_error",
                "Alguns campos estão inválidos.",
                request,
                {"fields": fields},
            ),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Erro inesperado em %s", request.url.path, exc_info=exc)
        return JSONResponse(
            status_code=500,
            content=_payload(
                "internal_error",
                "Erro interno. Consulte o log da aplicação para detalhes.",
                request,
            ),
        )
