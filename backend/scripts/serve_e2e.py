"""Sobe a API para os testes E2E com um banco descartável.

O banco fica em ``data/e2e/`` (ignorado pelo Git) e é recriado pelas migrations
reais a cada execução. Assim os testes nunca leem nem alteram ``data/gnzl.db``.
"""

from pathlib import Path
import sys

import uvicorn
from alembic import command
from alembic.config import Config

ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "backend"
MIGRATIONS_DIR = BACKEND_DIR / "migrations"
E2E_DB = ROOT / "data" / "e2e" / "gnzl-e2e.db"
HOST = "127.0.0.1"
PORT = 8100

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402


def prepare_database() -> str:
    """Remove o banco anterior e aplica todas as migrations."""
    E2E_DB.parent.mkdir(parents=True, exist_ok=True)
    for suffix in ("", "-wal", "-shm"):
        Path(f"{E2E_DB}{suffix}").unlink(missing_ok=True)

    database_url = f"sqlite:///{E2E_DB.as_posix()}"
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")
    return database_url


def main() -> None:
    settings = Settings(
        provider="demo",
        environment="dev",
        host=HOST,
        port=PORT,
        database_url=prepare_database(),
    )
    app = create_app(settings)

    print(f"gnzl achados E2E - banco: {E2E_DB}")
    print(f"API E2E: http://{HOST}:{PORT}/api/docs")
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")


if __name__ == "__main__":
    main()
