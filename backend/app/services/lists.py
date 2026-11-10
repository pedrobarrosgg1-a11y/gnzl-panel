"""Serviço de listas de produtos."""

from collections.abc import Sequence

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.models.product import Product, ProductList
from app.repositories import lists as lists_repo
from app.repositories import products as products_repo
from app.services.normalization import normalize_list_name


class ListService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, name: str, description: str | None) -> ProductList:
        normalized = normalize_list_name(name)
        if lists_repo.get_by_normalized_name(self._session, normalized):
            raise ConflictError("Já existe uma lista com esse nome.")

        product_list = lists_repo.create(
            self._session,
            name=name,
            normalized_name=normalized,
            description=description,
        )
        try:
            self._session.commit()
        except IntegrityError as error:
            self._session.rollback()
            raise ConflictError("Já existe uma lista com esse nome.") from error
        return product_list

    def list_with_counts(self) -> list[tuple[ProductList, int]]:
        return lists_repo.list_with_counts(self._session)

    def get(self, list_id: int) -> ProductList:
        product_list = lists_repo.get_by_id(self._session, list_id)
        if product_list is None:
            raise NotFoundError("Lista não encontrada.")
        return product_list

    def detail(self, list_id: int) -> tuple[ProductList, list[Product]]:
        product_list = self.get(list_id)
        return product_list, lists_repo.products_of(self._session, list_id)

    def update(
        self,
        list_id: int,
        *,
        name: str | None = None,
        description: str | None = None,
        update_description: bool = False,
    ) -> ProductList:
        product_list = self.get(list_id)

        if name is not None:
            normalized = normalize_list_name(name)
            duplicate = lists_repo.get_by_normalized_name(self._session, normalized)
            if duplicate is not None and duplicate.id != product_list.id:
                raise ConflictError("Já existe uma lista com esse nome.")
            product_list.name = name.strip()
            product_list.normalized_name = normalized

        if update_description:
            product_list.description = description

        try:
            self._session.commit()
        except IntegrityError as error:
            self._session.rollback()
            raise ConflictError("Já existe uma lista com esse nome.") from error
        return product_list

    def delete(self, list_id: int) -> None:
        product_list = self.get(list_id)
        lists_repo.delete(self._session, product_list)
        self._session.commit()

    def add_products(
        self, list_id: int, product_ids: Sequence[int]
    ) -> tuple[int, int]:
        """Adiciona produtos e informa quantos entraram e quantos já existiam."""
        self.get(list_id)

        unique_ids = list(dict.fromkeys(product_ids))
        found = products_repo.get_by_ids(self._session, unique_ids)
        found_ids = {product.id for product in found}
        missing = [product_id for product_id in unique_ids if product_id not in found_ids]
        if missing:
            raise ValidationError(
                "Alguns produtos não existem no catálogo local.",
                details={"missing_product_ids": missing},
            )

        existing = lists_repo.existing_product_ids(self._session, list_id)
        to_add = [product_id for product_id in unique_ids if product_id not in existing]
        lists_repo.add_items(self._session, list_id, to_add)
        self._session.commit()

        return len(to_add), len(unique_ids) - len(to_add)

    def remove_product(self, list_id: int, product_id: int) -> None:
        self.get(list_id)
        if not lists_repo.remove_item(self._session, list_id, product_id):
            raise NotFoundError("Produto não encontrado nesta lista.")
        self._session.commit()
