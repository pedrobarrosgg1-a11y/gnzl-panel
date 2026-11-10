"""Endpoints do histórico de links."""

from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.constants import MAX_PAGE_SIZE
from app.core.deps import get_db, get_providers, get_settings_from_app
from app.providers.registry import Providers
from app.schemas.links import LinkListResponse, LinkOut, LinkRegenerateRequest
from app.services.links import LinkService

router = APIRouter(prefix="/links", tags=["links"])

LinkStatus = Literal["active", "replaced"]


def _service(
    session: Session, providers: Providers, settings: Settings
) -> LinkService:
    return LinkService(
        session,
        providers.link,
        source=providers.source,
    )


@router.get("", response_model=LinkListResponse)
def list_links(
    q: str | None = Query(default=None, max_length=200),
    batch_id: int | None = Query(default=None, ge=1),
    link_status: LinkStatus | None = Query(default=None, alias="status"),
    sub_id_1: str | None = Query(default=None, max_length=64),
    sub_id_2: str | None = Query(default=None, max_length=64),
    sub_id_3: str | None = Query(default=None, max_length=64),
    data_source: Literal["demo", "shopee", "csv"] | None = Query(
        default=None, alias="source"
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=MAX_PAGE_SIZE),
    session: Session = Depends(get_db),
    providers: Providers = Depends(get_providers),
    settings: Settings = Depends(get_settings_from_app),
) -> LinkListResponse:
    links, total = _service(session, providers, settings).list_page(
        term=q.strip() if q and q.strip() else None,
        batch_id=batch_id,
        status=link_status,
        sub_id_1=sub_id_1,
        sub_id_2=sub_id_2,
        sub_id_3=sub_id_3,
        data_source=data_source,
        page=page,
        page_size=page_size,
    )
    return LinkListResponse(
        items=[LinkOut.from_model(link) for link in links],
        page=page,
        page_size=page_size,
        total=total,
        has_next=page * page_size < total,
    )


@router.get("/{link_id}", response_model=LinkOut)
def get_link(
    link_id: int,
    session: Session = Depends(get_db),
    providers: Providers = Depends(get_providers),
    settings: Settings = Depends(get_settings_from_app),
) -> LinkOut:
    link = _service(session, providers, settings).get(link_id)
    return LinkOut.from_model(link)


@router.post("/{link_id}/regenerate", response_model=LinkOut)
def regenerate_link(
    link_id: int,
    payload: LinkRegenerateRequest,
    session: Session = Depends(get_db),
    providers: Providers = Depends(get_providers),
    settings: Settings = Depends(get_settings_from_app),
) -> LinkOut:
    provided_fields = payload.model_fields_set
    sub_id_fields = {
        "sub_id_1",
        "sub_id_2",
        "sub_id_3",
        "sub_id_4",
        "sub_id_5",
    }
    sub_ids = (
        payload.sub_id_values() if provided_fields & sub_id_fields else None
    )
    link = _service(session, providers, settings).regenerate(
        link_id,
        sub_ids=sub_ids,
        observation=payload.observation,
        update_observation="observation" in provided_fields,
    )
    return LinkOut.from_model(link)
