"""Serviço de busca de produtos."""

from sqlalchemy.orm import Session

from app.core.errors import ValidationError
from app.models.product import Product
from app.providers.base import ProductPage, ProductProvider, ProductQuery
from app.repositories import products as products_repo


class ProductService:
    def __init__(self, session: Session, provider: ProductProvider) -> None:
        self._session = session
        self._provider = provider

    def search(self, query: ProductQuery) -> tuple[ProductPage, list[Product]]:
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
