"""Capacidades declaradas de cada provedor.

A interface não deve exibir controles que a fonte não sabe atender: filtrar no
frontend depois de buscar deixaria paginação e contagem erradas. Estas flags
são a única fonte da verdade para montar a tela de busca.
"""

from app.providers.base import SortOption, ProviderCapabilities

ALL_SORTS: tuple[SortOption, ...] = (
    "relevance",
    "commission_desc",
    "sales_desc",
    "rating_desc",
    "price_asc",
    "price_desc",
)

DEMO_CAPABILITIES = ProviderCapabilities(sorts=ALL_SORTS)

# A API oficial de afiliados não aceita preço, comissão nem categoria por nome
# e não expõe ordenação por avaliação.
SHOPEE_CAPABILITIES = ProviderCapabilities(
    category_filter=False,
    price_filter=False,
    commission_filter=False,
    sorts=(
        "relevance",
        "commission_desc",
        "sales_desc",
        "price_asc",
        "price_desc",
    ),
)
