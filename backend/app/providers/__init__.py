"""Provedores de dados (demo, Shopee, CSV) e seus contratos."""

from app.providers.base import (
    GeneratedLink,
    LinkProvider,
    ProductPage,
    ProductProvider,
    ProductQuery,
    ProductRecord,
)
from app.providers.registry import Providers, build_providers

__all__ = [
    "GeneratedLink",
    "LinkProvider",
    "ProductPage",
    "ProductProvider",
    "ProductQuery",
    "ProductRecord",
    "Providers",
    "build_providers",
]
