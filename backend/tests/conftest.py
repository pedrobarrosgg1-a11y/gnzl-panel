"""Fixtures compartilhadas dos testes.

Nenhum teste toca o banco de desenvolvimento: cada um recebe um SQLite
temporário criado pelas migrations reais.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import PROJECT_ROOT, Settings
from app.database.session import create_db_engine
from app.main import create_app
from app.providers.registry import build_providers

MIGRATIONS_DIR = PROJECT_ROOT / "backend" / "migrations"


@pytest.fixture
def settings() -> Settings:
    return Settings(provider="demo", environment="dev")


@pytest.fixture
def database_url(tmp_path: Path) -> Iterator[str]:
    """Banco temporário criado pelas migrations reais — não por create_all()."""
    url = f"sqlite:///{(tmp_path / 'gnzl-test.db').as_posix()}"
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", url)
    command.upgrade(config, "head")
    yield url


@pytest.fixture
def engine(database_url: str) -> Iterator[Engine]:
    engine = create_db_engine(database_url)
    yield engine
    engine.dispose()


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    factory = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    session = factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(engine: Engine, settings: Settings) -> Iterator[TestClient]:
    """Cliente HTTP ligado ao banco temporário e ao provedor demo."""
    providers = build_providers(settings)
    with TestClient(create_app(settings, providers=providers, engine=engine)) as client:
        yield client
