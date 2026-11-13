"""Serviço de busca de produtos."""

from sqlalchemy.orm import Session

from app.core.errors import ValidationError
from app.models.product import Product
from app.providers.base import (
    ProductPage,
    ProductProvider,
    ProductQuery,
    ProviderCapabilities,
)
from app.providers.capabilities import DEMO_CAPABILITIES
from app.repositories import products as products_repo


class ProductService:
    def __init__(
        self,
        session: Session,
        provider: ProductProvider,
        capabilities: ProviderCapabilities | None = None,
    ) -> None:
        self._session = session
        self._provider = provider
        self._capabilities = capabilities or DEMO_CAPABILITIES

    def search(self, query: ProductQuery) -> tuple[ProductPage, list[Product]]:
        self._reject_unsupported_filters(query)

        if (
            query.price_min_cents is not None
            and query.price_max_cents is not None
            and query.price_min_cents > query.price_max_cents
        ):
            raise ValidationError(
                "O preço mínimo não pode ser maior que o preço máximo.",
                details={"price_min_cents": query.price_min_cents,
                         "price_max_cents": query.price_max_cents},
            )

        page = self._provider.search_products(query)
        # Guardar o que foi visto mantém listas e histórico independentes da
        # disponibilidade do provedor no futuro.
        products = products_repo.upsert_records(self._session, page.items)
        self._session.commit()
        return page, products

    def categories(self) -> list[str]:
        seen: dict[str, str] = {}

        for category in self._provider.list_categories():
            cleaned = category.strip()
            if cleaned:
                seen.setdefault(cleaned.casefold(), cleaned)

        for category in products_repo.distinct_categories(
            self._session, self._provider.name
        ):
            seen.setdefault(category.casefold(), category)

        return sorted(seen.values(), key=str.casefold)

    def _reject_unsupported_filters(self, query: ProductQuery) -> None:
        unsupported: dict[str, str] = {}

        if query.category and not self._capabilities.category_filter:
            unsupported["category"] = (
                "O provedor atual não permite filtrar por categoria."
            )
        if (
            query.price_min_cents is not None
            or query.price_max_cents is not None
        ) and not self._capabilities.price_filter:
            unsupported["price"] = (
                "O provedor atual não permite filtrar por preço."
            )
        if (
            query.min_commission_rate_bp is not None
            and not self._capabilities.commission_filter
        ):
            unsupported["min_commission_rate_bp"] = (
                "O provedor atual não permite filtrar por comissão mínima."
            )
        if query.sort not in self._capabilities.sorts:
            unsupported["sort"] = (
                "O provedor atual não permite ordenar por este critério."
            )

        if unsupported:
            raise ValidationError(
                "Um ou mais filtros não são suportados pelo provedor atual.",
                details={"unsupported": unsupported},
            )
