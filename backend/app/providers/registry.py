"""Montagem dos provedores a partir da configuração.

Nunca há fallback silencioso: se o provedor configurado não estiver pronto, a
aplicação falha no startup com uma mensagem que diz o que fazer.
"""

from dataclasses import dataclass

from app.core.config import Settings
from app.core.errors import ConfigurationError
from app.providers.base import (
    LinkProvider,
    ProductProvider,
    ProviderCapabilities,
)
from app.providers.capabilities import DEMO_CAPABILITIES, SHOPEE_CAPABILITIES
from app.providers.demo import DemoProvider
from app.providers.shopee import ShopeeClient, ShopeeProvider


@dataclass(frozen=True)
class Providers:
    product: ProductProvider
    link: LinkProvider
    source: str
    capabilities: ProviderCapabilities = DEMO_CAPABILITIES


def build_providers(settings: Settings) -> Providers:
    if settings.provider == "shopee":
        if not settings.shopee_app_id or not settings.shopee_secret:
            raise ConfigurationError(
                "GNZL_PROVIDER=shopee exige GNZL_SHOPEE_APP_ID e GNZL_SHOPEE_SECRET no .env."
            )
        client = ShopeeClient(
            app_id=settings.shopee_app_id,
            secret=settings.shopee_secret,
            api_base=settings.shopee_api_base,
            timeout=settings.http_timeout_seconds,
        )
        provider = ShopeeProvider(client)
        return Providers(
            product=provider,
            link=provider,
            source=provider.name,
            capabilities=SHOPEE_CAPABILITIES,
        )

    demo = DemoProvider()
    return Providers(
        product=demo,
        link=demo,
        source=demo.name,
        capabilities=DEMO_CAPABILITIES,
    )
