"""Endpoints de listas de produtos."""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.schemas.lists import (
    AddItemsRequest,
    AddItemsResponse,
    ListCreateRequest,
    ListDetail,
    ListSummary,
    ListUpdateRequest,
)
from app.schemas.products import ProductOut
from app.services.lists import ListService

router = APIRouter(prefix="/lists", tags=["listas"])


@router.get("", response_model=list[ListSummary])
def list_lists(session: Session = Depends(get_db)) -> list[ListSummary]:
    service = ListService(session)
    return [
        ListSummary.from_model(product_list, item_count)
        for product_list, item_count in service.list_with_counts()
    ]


@router.post("", response_model=ListSummary, status_code=status.HTTP_201_CREATED)
def create_list(
    payload: ListCreateRequest, session: Session = Depends(get_db)
) -> ListSummary:
    service = ListService(session)
    product_list = service.create(payload.name, payload.description)
    return ListSummary.from_model(product_list, 0)


@router.get("/{list_id}", response_model=ListDetail)
def get_list(list_id: int, session: Session = Depends(get_db)) -> ListDetail:
    service = ListService(session)
    product_list, products = service.detail(list_id)

    summary = ListSummary.from_model(product_list, len(products))
    return ListDetail(
        **summary.model_dump(),
        items=[ProductOut.from_model(product) for product in products],
    )


@router.patch("/{list_id}", response_model=ListSummary)
def update_list(
    list_id: int,
    payload: ListUpdateRequest,
    session: Session = Depends(get_db),
) -> ListSummary:
    service = ListService(session)
    product_list = service.update(
        list_id,
        name=payload.name,
        description=payload.description,
        update_description="description" in payload.model_fields_set,
    )
    _, products = service.detail(list_id)
    return ListSummary.from_model(product_list, len(products))


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_list(list_id: int, session: Session = Depends(get_db)) -> Response:
    ListService(session).delete(list_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{list_id}/items", response_model=AddItemsResponse)
def add_items(
    list_id: int,
    payload: AddItemsRequest,
    session: Session = Depends(get_db),
) -> AddItemsResponse:
    service = ListService(session)
    added, skipped = service.add_products(list_id, payload.product_ids)
    _, products = service.detail(list_id)
    return AddItemsResponse(
        added=added,
        skipped=skipped,
        item_count=len(products),
        items=[ProductOut.from_model(product) for product in products],
    )


@router.delete("/{list_id}/items/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_item(
    list_id: int, product_id: int, session: Session = Depends(get_db)
) -> Response:
    ListService(session).remove_product(list_id, product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
