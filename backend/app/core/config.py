"""Configuração da aplicação.

Todas as variáveis de ambiente usam o prefixo ``GNZL_`` e são lidas de um
arquivo ``.env`` na raiz do projeto. O arquivo é opcional: os valores padrão
permitem rodar a aplicação em modo demo sem nenhuma configuração extra.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_SHOPEE_API_BASE = "https://open-api.affiliate.shopee.com.br/graphql"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="GNZL_",
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Literal["dev", "prod"] = "dev"
    provider: Literal["demo", "shopee"] = "demo"

    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)

    data_dir: Path = DEFAULT_DATA_DIR
    database_url: str | None = None

    link_concurrency: int = Field(default=3, ge=1, le=10)
    http_timeout_seconds: float = Field(default=15.0, gt=0, le=120)

    shopee_app_id: str = ""
    shopee_secret: str = ""
    shopee_api_base: str = DEFAULT_SHOPEE_API_BASE

    @property
    def is_demo(self) -> bool:
        return self.provider == "demo"

    @property
    def resolved_database_url(self) -> str:
        """URL do SQLite com caminho absoluto, para não depender do diretório atual."""
        if self.database_url:
            return self.database_url
        return f"sqlite:///{(self.data_dir / 'gnzl.db').as_posix()}"

    def ensure_data_dir(self) -> Path:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return self.data_dir


@lru_cache
def get_settings() -> Settings:
    return Settings()
