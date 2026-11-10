"""Endpoints de lotes de geração de links."""

from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.constants import MAX_PAGE_SIZE
from app.core.deps import get_db, get_providers, get_settings_from_app
from app.providers.registry import Providers
from app.schemas.link_batches import (
    BatchStatus,
    LinkBatchCreateRequest,
    LinkBatchDetail,
    LinkBatchListResponse,
    LinkBatchSummary,
)
from app.services.link_batches import LinkBatchService

router = APIRouter(prefix="/link-batches", tags=["lotes"])


def _service(
    session: Session, providers: Providers, settings: Settings
) -> LinkBatchService:
    return LinkBatchService(
        session,
        providers.link,
        source=providers.source,
        concurrency=settings.link_concurrency,
    )


@router.get("", response_model=LinkBatchListResponse)
def list_batches(
    batch_status: BatchStatus | None = Query(default=None, alias="status"),
    data_source: Literal["demo", "shopee", "csv"] | None = Query(
        default=None, alias="source"
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=MAX_PAGE_SIZE),
    session: Session = Depends(get_db),
    providers: Providers = Depends(get_providers),
    settings: Settings = Depends(get_settings_from_app),
) -> LinkBatchListResponse:
    batches, total = _service(session, providers, settings).list_page(
        status=batch_status,
        data_source=data_source,
        page=page,
        page_size=page_size,
    )
    return LinkBatchListResponse(
        items=[LinkBatchSummary.from_model(batch) for batch in batches],
        page=page,
        page_size=page_size,
        total=total,
        has_next=page * page_size < total,
    )


@router.post("", response_model=LinkBatchDetail, status_code=status.HTTP_201_CREATED)
def create_batch(
    payload: LinkBatchCreateRequest,
    session: Session = Depends(get_db),
    providers: Providers = Depends(get_providers),
    settings: Settings = Depends(get_settings_from_app),
) -> LinkBatchDetail:
    batch = _service(session, providers, settings).create(
        name=payload.name,
        destination_type=payload.destination_type,
        product_ids=payload.product_ids,
        product_list_id=payload.product_list_id,
        observation=payload.observation,
        sub_ids=payload.sub_id_values(),
    )
    return LinkBatchDetail.from_model(batch)


@router.get("/{batch_id}", response_model=LinkBatchDetail)
def get_batch(
    batch_id: int,
    session: Session = Depends(get_db),
    providers: Providers = Depends(get_providers),
    settings: Settings = Depends(get_settings_from_app),
) -> LinkBatchDetail:
    batch = _service(session, providers, settings).detail(batch_id)
    return LinkBatchDetail.from_model(batch)


@router.post("/{batch_id}/run", response_model=LinkBatchDetail)
def run_batch(
    batch_id: int,
    session: Session = Depends(get_db),
    providers: Providers = Depends(get_providers),
    settings: Settings = Depends(get_settings_from_app),
) -> LinkBatchDetail:
    batch = _service(session, providers, settings).run(batch_id)
    return LinkBatchDetail.from_model(batch)
