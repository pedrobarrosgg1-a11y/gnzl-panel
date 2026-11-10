"""Schemas de lotes de geração de links."""

from typing import Literal

from pydantic import BaseModel, Field

from app.models.link import LinkBatch, LinkBatchItem
from app.schemas.common import UtcDateTime
from app.schemas.products import ProductOut

DestinationType = Literal["product", "list"]
BatchStatus = Literal["pending", "running", "completed", "partial", "failed"]


class LinkBatchCreateRequest(BaseModel):
    """Configuração do lote. Os Sub IDs valem para todos os itens.

    O limite de 200 na entrada permite que a normalização corte para o teto do
    banco (64) sem devolver erro de tamanho antes da limpeza.
    """

    name: str | None = Field(default=None, max_length=160)
    destination_type: DestinationType
    product_ids: list[int] = Field(default_factory=list)
    product_list_id: int | None = None
    observation: str | None = Field(default=None, max_length=2000)
    sub_id_1: str | None = Field(default=None, max_length=200)
    sub_id_2: str | None = Field(default=None, max_length=200)
    sub_id_3: str | None = Field(default=None, max_length=200)
    sub_id_4: str | None = Field(default=None, max_length=200)
    sub_id_5: str | None = Field(default=None, max_length=200)

    def sub_id_values(self) -> tuple[str | None, ...]:
        return (
            self.sub_id_1,
            self.sub_id_2,
            self.sub_id_3,
            self.sub_id_4,
            self.sub_id_5,
        )


class LinkBatchItemOut(BaseModel):
    id: int
    product_id: int | None
    product: ProductOut | None
    original_url: str
    status: str
    affiliate_link_id: int | None
    affiliate_url: str | None
    error_code: str | None
    error_message: str | None
    attempts: int
    processed_at: UtcDateTime | None
    created_at: UtcDateTime

    @classmethod
    def from_model(cls, item: LinkBatchItem) -> "LinkBatchItemOut":
        return cls(
            id=item.id,
            product_id=item.product_id,
            product=ProductOut.from_model(item.product) if item.product else None,
            original_url=item.original_url,
            status=item.status,
            affiliate_link_id=item.affiliate_link_id,
            affiliate_url=(
                item.affiliate_link.affiliate_url if item.affiliate_link else None
            ),
            error_code=item.error_code,
            error_message=item.error_message,
            attempts=item.attempts,
            processed_at=item.processed_at,
            created_at=item.created_at,
        )


class LinkBatchSummary(BaseModel):
    id: int
    name: str | None
    destination_type: str
    product_list_id: int | None
    observation: str | None
    sub_id_1: str | None
    sub_id_2: str | None
    sub_id_3: str | None
    sub_id_4: str | None
    sub_id_5: str | None
    source: str
    is_demo: bool
    total_items: int
    successful_items: int
    failed_items: int
    status: str
    created_at: UtcDateTime
    finished_at: UtcDateTime | None

    @classmethod
    def from_model(cls, batch: LinkBatch) -> "LinkBatchSummary":
        return cls(
            id=batch.id,
            name=batch.name,
            destination_type=batch.destination_type,
            product_list_id=batch.product_list_id,
            observation=batch.observation,
            sub_id_1=batch.sub_id_1,
            sub_id_2=batch.sub_id_2,
            sub_id_3=batch.sub_id_3,
            sub_id_4=batch.sub_id_4,
            sub_id_5=batch.sub_id_5,
            source=batch.data_source,
            is_demo=batch.data_source == "demo",
            total_items=batch.total_items,
            successful_items=batch.successful_items,
            failed_items=batch.failed_items,
            status=batch.status,
            created_at=batch.created_at,
            finished_at=batch.finished_at,
        )


class LinkBatchDetail(LinkBatchSummary):
    items: list[LinkBatchItemOut]

    @classmethod
    def from_model(cls, batch: LinkBatch) -> "LinkBatchDetail":
        summary = LinkBatchSummary.from_model(batch)
        return cls(
            **summary.model_dump(),
            items=[LinkBatchItemOut.from_model(item) for item in batch.items],
        )


class LinkBatchListResponse(BaseModel):
    items: list[LinkBatchSummary]
    page: int
    page_size: int
    total: int
    has_next: bool
