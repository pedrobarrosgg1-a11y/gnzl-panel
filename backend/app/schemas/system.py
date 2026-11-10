"""Schemas da API do sistema (saúde e configuração pública)."""

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"]
    version: str


class ConfigResponse(BaseModel):
    """Informações que o frontend precisa para se apresentar corretamente.

    Não inclui credenciais nem detalhes internos do provedor.
    """

    version: str
    environment: Literal["dev", "prod"]
    provider: Literal["demo", "shopee"]
    is_demo: bool
