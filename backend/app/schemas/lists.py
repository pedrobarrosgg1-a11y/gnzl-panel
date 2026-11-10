"""Schemas de listas de produtos."""

from pydantic import BaseModel, Field

from app.core.constants import LIST_NAME_MAX_LENGTH
from app.models.product import ProductList
from app.schemas.common import UtcDateTime
from app.schemas.products import ProductOut


class ListCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=LIST_NAME_MAX_LENGTH)
    description: str | None = Field(default=None, max_length=500)


class ListUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=LIST_NAME_MAX_LENGTH)
    description: str | None = Field(default=None, max_length=500)


class ListSummary(BaseModel):
    id: int
    name: str
    description: str | None
    item_count: int
    created_at: UtcDateTime
    updated_at: UtcDateTime

    @classmethod
    def from_model(cls, product_list: ProductList, item_count: int) -> "ListSummary":
        return cls(
            id=product_list.id,
            name=product_list.name,
            description=product_list.description,
            item_count=item_count,
            created_at=product_list.created_at,
            updated_at=product_list.updated_at,
        )


class ListDetail(ListSummary):
    items: list[ProductOut]


class AddItemsRequest(BaseModel):
    product_ids: list[int] = Field(min_length=1)


class AddItemsResponse(BaseModel):
    added: int
    skipped: int
    item_count: int
    items: list[ProductOut]
