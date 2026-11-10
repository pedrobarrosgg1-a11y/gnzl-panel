"""Montagem dos provedores a partir da configuração.

Nunca há fallback silencioso: se o provedor configurado não estiver pronto, a
aplicação falha no startup com uma mensagem que diz o que fazer.
"""

from dataclasses import dataclass

from app.core.config import Settings
from app.core.errors import ConfigurationError
from app.providers.base import LinkProvider, ProductProvider
from app.providers.demo import DemoProvider


@dataclass(frozen=True)
class Providers:
    product: ProductProvider
    link: LinkProvider
    source: str


def build_providers(settings: Settings) -> Providers:
    if settings.provider == "shopee":
        if not settings.shopee_app_id or not settings.shopee_secret:
            raise ConfigurationError(
                "GNZL_PROVIDER=shopee exige GNZL_SHOPEE_APP_ID e GNZL_SHOPEE_SECRET no .env."
            )
        raise ConfigurationError(
            "O provedor oficial ainda não foi implementado. "
            "Use GNZL_PROVIDER=demo até a integração ser validada."
        )

    demo = DemoProvider()
    return Providers(product=demo, link=demo, source=demo.name)
