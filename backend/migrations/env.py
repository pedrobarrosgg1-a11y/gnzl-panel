"""Configuração do Alembic.

A URL do banco vem das settings da aplicação (``GNZL_DATABASE_URL`` ou
``data/gnzl.db``). Em testes, a URL é injetada via ``config.get_main_option``.
"""

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import get_settings  # noqa: E402
from app.database.base import Base  # noqa: E402
from app.database.session import create_db_engine  # noqa: E402
import app.models  # noqa: E402,F401  (registra as tabelas no metadata)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

_PLACEHOLDER_URL = "driver://user:pass@localhost/dbname"


def _database_url() -> str:
    configured = config.get_main_option("sqlalchemy.url")
    if configured and configured != _PLACEHOLDER_URL:
        return configured
    return get_settings().resolved_database_url


def run_migrations_offline() -> None:
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_db_engine(_database_url())

    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # SQLite não altera colunas com ALTER TABLE; batch recria a tabela
            # preservando os dados nas evoluções futuras.
            render_as_batch=True,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()

    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
