"""Engine, sessão e pragmas do SQLite.

Decisões:
- ``check_same_thread=False`` é necessário porque o FastAPI executa endpoints
  síncronos em threadpool e cada requisição pode cair em uma thread diferente.
- ``foreign_keys=ON`` é obrigatório: o SQLite aceita a cláusula FK, mas só
  valida se o pragma estiver ligado em cada conexão.
- ``journal_mode=WAL`` melhora leitura concorrente e reduz locks. Se o sistema
  de arquivos não suportar (ex.: pasta de rede), seguimos com o modo padrão em
  vez de derrubar a aplicação.
"""

from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings


def _configure_sqlite(engine: Engine) -> None:
    @event.listens_for(engine, "connect")
    def _set_pragmas(dbapi_connection, _connection_record) -> None:  # noqa: ANN001
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA busy_timeout=5000")
            cursor.execute("PRAGMA synchronous=NORMAL")
            try:
                cursor.execute("PRAGMA journal_mode=WAL")
            except Exception:  # noqa: BLE001 - pragma opcional, depende do filesystem
                pass
        finally:
            cursor.close()


def create_db_engine(url: str) -> Engine:
    is_sqlite = url.startswith("sqlite")

    if is_sqlite:
        # Garante que o diretório do arquivo exista antes do primeiro acesso.
        path = url.removeprefix("sqlite:///")
        if path and path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(
        url,
        connect_args={"check_same_thread": False} if is_sqlite else {},
        pool_pre_ping=True,
        future=True,
    )

    if is_sqlite:
        _configure_sqlite(engine)

    return engine


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


def build_database(settings: Settings) -> tuple[Engine, sessionmaker[Session]]:
    settings.ensure_data_dir()
    engine = create_db_engine(settings.resolved_database_url)
    return engine, create_session_factory(engine)


def get_db(engine: Engine) -> Iterator[Session]:
    """Dependência do FastAPI: uma sessão por requisição."""
    factory = create_session_factory(engine)
    session = factory()
    try:
        yield session
    finally:
        session.close()
