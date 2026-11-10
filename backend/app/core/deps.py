"""Dependências compartilhadas dos endpoints."""

from collections.abc import Iterator

from fastapi import Request
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.providers.registry import Providers


def get_settings_from_app(request: Request) -> Settings:
    return request.app.state.settings


def get_providers(request: Request) -> Providers:
    return request.app.state.providers


def get_db(request: Request) -> Iterator[Session]:
    """Uma sessão por requisição, sempre fechada ao final."""
    session = request.app.state.session_factory()
    try:
        yield session
    finally:
        session.close()
