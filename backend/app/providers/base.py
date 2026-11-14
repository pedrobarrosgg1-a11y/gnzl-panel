"""Contrato dos provedores de dados.

Os serviços conhecem apenas estes tipos. Trocar demo por Shopee (ou CSV) não
altera regra de negócio nem a API HTTP.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal, Protocol, runtime_checkable

from app.core.constants import MAX_CONVERSION_WINDOW_DAYS

SortOption = Literal[
    "relevance",
    "commission_desc",
    "sales_desc",
    "rating_desc",
    "price_asc",
    "price_desc",
]

SOURCE_DEMO = "demo"
SOURCE_SHOPEE = "shopee"
SOURCE_CSV = "csv"


@dataclass(frozen=True)
class ProductQuery:
    keyword: str | None = None
    category: str | None = None
    price_min_cents: int | None = None
    price_max_cents: int | None = None
    min_commission_rate_bp: int | None = None
    sort: SortOption = "relevance"
    page: int = 1
    page_size: int = 20


@dataclass(frozen=True)
class ProviderCapabilities:
    """O que a fonte de dados sabe atender sem filtragem local enganosa."""

    category_filter: bool = True
    price_filter: bool = True
    commission_filter: bool = True
    sorts: tuple[SortOption, ...] = (
        "relevance",
        "commission_desc",
        "sales_desc",
        "rating_desc",
        "price_asc",
        "price_desc",
    )
    conversion_sync: bool = False
    conversion_window_days: int = MAX_CONVERSION_WINDOW_DAYS


@dataclass(frozen=True)
class ProductRecord:
    """Produto normalizado, independente do formato da fonte.

    Campos que a fonte não informa ficam ``None`` — nunca zero inventado.
    """

    item_id: int
    shop_id: int
    title: str
    product_url: str
    price_cents: int
    commission_rate_bp: int
    image_url: str | None = None
    sales: int | None = None
    rating_x100: int | None = None
    category: str | None = None
    source: str = SOURCE_DEMO


@dataclass(frozen=True)
class ProductPage:
    items: list[ProductRecord] = field(default_factory=list)
    page: int = 1
    page_size: int = 20
    has_next: bool = False
    total: int | None = None


@dataclass(frozen=True)
class GeneratedLink:
    original_url: str
    affiliate_url: str
    source: str


@dataclass(frozen=True)
class ConversionQuery:
    """Janela de compra consultada na fonte, em UTC sem timezone."""

    start: datetime
    end: datetime


@dataclass(frozen=True)
class ConversionRecord:
    """Uma linha de item do relatório de conversões, já normalizada.

    ``dedup_key`` é estável dentro da origem e identifica pedido + item +
    variante. ``raw`` guarda a resposta original para auditoria; nunca é usado
    nas regras de negócio.
    """

    external_order_id: str
    external_item_id: int | None
    shop_id: int | None
    title: str | None
    image_url: str | None
    status: str
    status_group: str
    ordered_at: datetime
    completed_at: datetime | None
    quantity: int
    sales_cents: int
    commission_cents: int
    sub_ids: tuple[str | None, ...]
    channel: str | None
    dedup_key: str
    source: str = SOURCE_DEMO
    raw: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class ProductProvider(Protocol):
    name: str
    is_demo: bool

    def search_products(self, query: ProductQuery) -> ProductPage: ...

    def list_categories(self) -> list[str]:
        """Categorias conhecidas pela fonte. Lista vazia quando não houver."""
        ...


@runtime_checkable
class LinkProvider(Protocol):
    name: str
    is_demo: bool

    def create_link(self, origin_url: str, sub_ids: tuple[str, ...]) -> GeneratedLink: ...


@runtime_checkable
class ConversionProvider(Protocol):
    name: str
    is_demo: bool
    conversion_window_days: int

    def fetch_conversions(
        self, query: ConversionQuery
    ) -> list[ConversionRecord]:
        """Devolve todas as linhas da janela, seguindo a paginação da fonte."""
        ...
