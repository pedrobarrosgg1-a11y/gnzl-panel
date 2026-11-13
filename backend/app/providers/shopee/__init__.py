"""Integração com a Open API de afiliados da Shopee."""

from app.providers.shopee.client import ShopeeClient
from app.providers.shopee.provider import ShopeeProvider

__all__ = ["ShopeeClient", "ShopeeProvider"]
