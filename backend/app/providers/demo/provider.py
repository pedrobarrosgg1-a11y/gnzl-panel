"""Provedor de demonstração: dados fictícios, sem rede."""

import hashlib
import unicodedata

from app.core.errors import ProviderUnavailable, ValidationError
from app.providers.base import (
    SOURCE_DEMO,
    GeneratedLink,
    ProductPage,
    ProductQuery,
    ProductRecord,
)
from app.providers.demo.catalog import DEMO_FAILING_ITEM_ID, DEMO_PRODUCTS

MAX_PAGE_SIZE = 100


def _fold(value: str) -> str:
    """Minúsculas e sem acento, para busca tolerante em português."""
    normalized = unicodedata.normalize("NFKD", value)
    return normalized.encode("ascii", "ignore").decode("ascii").casefold()


def _matches(record: ProductRecord, query: ProductQuery) -> bool:
    if query.keyword:
        needle = _fold(query.keyword).strip()
        if needle:
            haystack = _fold(f"{record.title} {record.category or ''}")
            if needle not in haystack:
                return False
    if query.category and _fold(query.category) != _fold(record.category or ""):
        return False
    if query.price_min_cents is not None and record.price_cents < query.price_min_cents:
        return False
    if query.price_max_cents is not None and record.price_cents > query.price_max_cents:
        return False
    if (
        query.min_commission_rate_bp is not None
        and record.commission_rate_bp < query.min_commission_rate_bp
    ):
        return False
    return True


def _sort_key(record: ProductRecord, sort: str) -> tuple:
    if sort == "commission_desc":
        return (-record.commission_rate_bp,)
    if sort == "sales_desc":
        return (-(record.sales or 0),)
    if sort == "rating_desc":
        return (-(record.rating_x100 or 0),)
    if sort == "price_asc":
        return (record.price_cents,)
    if sort == "price_desc":
        return (-record.price_cents,)
    return ()


class DemoProvider:
    """Implementa ProductProvider e LinkProvider com resultados determinísticos."""

    name = SOURCE_DEMO
    is_demo = True

    def __init__(self, catalog: tuple[ProductRecord, ...] = DEMO_PRODUCTS) -> None:
        self._catalog = catalog

    def search_products(self, query: ProductQuery) -> ProductPage:
        if query.page < 1:
            raise ValidationError("A página deve ser maior ou igual a 1.")
        if not 1 <= query.page_size <= MAX_PAGE_SIZE:
            raise ValidationError(
                f"O tamanho da página deve estar entre 1 e {MAX_PAGE_SIZE}.", 
                details={"page_size": query.page_size},
            )

        filtered = [record for record in self._catalog if _matches(record, query)]
        if query.sort != "relevance":
            filtered.sort(key=lambda record: _sort_key(record, query.sort))

        start = (query.page - 1) * query.page_size
        end = start + query.page_size
        items = filtered[start:end]

        return ProductPage(
            items=items,
            page=query.page,
            page_size=query.page_size,
            has_next=end < len(filtered),
            total=len(filtered),
        )

    def create_link(self, origin_url: str, sub_ids: tuple[str, ...]) -> GeneratedLink:
        origin_url = origin_url.strip()
        if not origin_url:
            raise ValidationError("A URL de origem é obrigatória.")
        if len(sub_ids) > 5:
            raise ValidationError("São permitidos no máximo 5 Sub IDs.")

        if origin_url.rstrip("/").endswith(f".{DEMO_FAILING_ITEM_ID}"):
            raise ProviderUnavailable(
                "Falha simulada do modo demo: este produto sempre falha na geração."
            )

        digest = hashlib.sha256(f"{origin_url}|{','.join(sub_ids)}".encode()).hexdigest()
        return GeneratedLink(
            original_url=origin_url,
            affiliate_url=f"https://demo.gnzl.local/r/{digest[:12]}",
            source=SOURCE_DEMO,
        )

    def list_categories(self) -> list[str]:
        seen: dict[str, str] = {}
        for record in self._catalog:
            if record.category:
                seen.setdefault(record.category.casefold(), record.category)
        return sorted(seen.values(), key=str.casefold)
