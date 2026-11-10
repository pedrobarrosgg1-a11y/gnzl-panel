"""Schemas do histórico de links."""

from pydantic import BaseModel, Field

from app.models.link import AffiliateLink
from app.schemas.common import UtcDateTime
from app.schemas.products import ProductOut


class LinkOut(BaseModel):
    id: int
    product_id: int | None
    product: ProductOut | None
    link_batch_id: int | None
    original_url: str
    affiliate_url: str
    sub_id_1: str | None
    sub_id_2: str | None
    sub_id_3: str | None
    sub_id_4: str | None
    sub_id_5: str | None
    observation: str | None
    status: str
    replaced_by_id: int | None
    source: str
    is_demo: bool
    created_at: UtcDateTime

    @classmethod
    def from_model(cls, link: AffiliateLink) -> "LinkOut":
        return cls(
            id=link.id,
            product_id=link.product_id,
            product=ProductOut.from_model(link.product) if link.product else None,
            link_batch_id=link.link_batch_id,
            original_url=link.original_url,
            affiliate_url=link.affiliate_url,
            sub_id_1=link.sub_id_1,
            sub_id_2=link.sub_id_2,
            sub_id_3=link.sub_id_3,
            sub_id_4=link.sub_id_4,
            sub_id_5=link.sub_id_5,
            observation=link.observation,
            status=link.status,
            replaced_by_id=link.replaced_by_id,
            source=link.data_source,
            is_demo=link.data_source == "demo",
            created_at=link.created_at,
        )


class LinkListResponse(BaseModel):
    items: list[LinkOut]
    page: int
    page_size: int
    total: int
    has_next: bool


class LinkRegenerateRequest(BaseModel):
    """Novos Sub IDs opcionais.

    Se qualquer campo de Sub ID for enviado, o conjunto completo substitui a
    configuração atual — posições omitidas ficam vazias. Se nenhum for enviado,
    a configuração atual é reaproveitada, e a operação falha porque isso gera
    exatamente a mesma URL.
    """

    sub_id_1: str | None = Field(default=None, max_length=200)
    sub_id_2: str | None = Field(default=None, max_length=200)
    sub_id_3: str | None = Field(default=None, max_length=200)
    sub_id_4: str | None = Field(default=None, max_length=200)
    sub_id_5: str | None = Field(default=None, max_length=200)
    observation: str | None = Field(default=None, max_length=2000)

    def sub_id_values(self) -> tuple[str | None, ...]:
        return (
            self.sub_id_1,
            self.sub_id_2,
            self.sub_id_3,
            self.sub_id_4,
            self.sub_id_5,
        )
