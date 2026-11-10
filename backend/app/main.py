"""Aplicação FastAPI do Gnzl Achados."""

import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Engine

from app import __version__
from app.api import link_batches, links, lists, products, sub_ids, system
from app.api.errors import register_error_handlers
from app.core.config import Settings, get_settings
from app.database.session import build_database, create_session_factory
from app.providers.registry import Providers, build_providers

# Apenas as origens usadas pelo servidor de desenvolvimento do Vite.
DEV_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


def create_app(
    settings: Settings | None = None,
    providers: Providers | None = None,
    engine: Engine | None = None,
) -> FastAPI:
    """Cria a aplicação.

    Receber ``settings``, ``providers`` e ``engine`` mantém os testes
    independentes do ``.env`` e do banco de desenvolvimento.
    """
    current_settings = settings or get_settings()
    current_providers = providers or build_providers(current_settings)

    if engine is None:
        engine, session_factory = build_database(current_settings)
    else:
        session_factory = create_session_factory(engine)

    app = FastAPI(
        title="gnzl achados",
        version=__version__,
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )
    app.state.settings = current_settings
    app.state.providers = current_providers
    app.state.engine = engine
    app.state.session_factory = session_factory

    # Toda dependência que pedir `get_settings` recebe as settings desta
    # instância. Sem isso, testes e execuções com configuração própria
    # acabariam lendo o cache global.
    app.dependency_overrides[get_settings] = lambda: current_settings

    if current_settings.environment == "dev":
        # Em produção local o frontend é servido pela mesma origem, então CORS
        # não é necessário. Restringir ao dev reduz a superfície exposta.
        app.add_middleware(
            CORSMiddleware,
            allow_origins=DEV_CORS_ORIGINS,
            allow_credentials=False,
            allow_methods=["GET", "POST", "PATCH", "DELETE"],
            allow_headers=["Content-Type"],
        )

    @app.middleware("http")
    async def attach_request_id(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    register_error_handlers(app)
    app.include_router(system.router, prefix="/api")
    app.include_router(products.router, prefix="/api")
    app.include_router(lists.router, prefix="/api")
    app.include_router(sub_ids.router, prefix="/api")
    app.include_router(link_batches.router, prefix="/api")
    app.include_router(links.router, prefix="/api")
    return app


app = create_app()
