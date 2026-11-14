"""Schemas da API do sistema (saúde e configuração pública)."""

from typing import Literal

from pydantic import BaseModel

from app.providers.base import SortOption


class HealthResponse(BaseModel):
    status: Literal["ok"]
    version: str


class CapabilitiesResponse(BaseModel):
    """O que a fonte de dados atual sabe atender."""

    category_filter: bool
    price_filter: bool
    commission_filter: bool
    conversion_sync: bool
    conversion_window_days: int
    sorts: list[SortOption]


class ConfigResponse(BaseModel):
    """Informações que o frontend precisa para se apresentar corretamente.

    Não inclui credenciais nem detalhes internos do provedor.
    """

    version: str
    environment: Literal["dev", "prod"]
    provider: Literal["demo", "shopee"]
    is_demo: bool
    capabilities: CapabilitiesResponse
