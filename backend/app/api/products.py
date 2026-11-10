"""Endpoints de busca de produtos."""

from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.constants import MAX_PAGE_SIZE
from app.core.deps import get_db, get_providers
from app.providers.base import ProductQuery
from app.providers.registry import Providers
from app.schemas.products import (
    CategoriesResponse,
    ProductOut,
    ProductSearchResponse,
)
from app.services.products import ProductService

router = APIRouter(prefix="/products", tags=["produtos"])

SortParam = Literal[
    "relevance",
    "commission_desc",
    "sales_desc",
    "rating_desc",
    "price_asc",
    "price_desc",
]


@router.get("/search", response_model=ProductSearchResponse)
def search_products(
    q: str | None = Query(default=None, max_length=120),
    category: str | None = Query(default=None, max_length=120),
    price_min_cents: int | None = Query(default=None, ge=0),
    price_max_cents: int | None = Query(default=None, ge=0),
    min_commission_rate_bp: int | None = Query(default=None, ge=0, le=10000),
    sort: SortParam = Query(default="relevance"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=MAX_PAGE_SIZE),
    session: Session = Depends(get_db),
    providers: Providers = Depends(get_providers),
) -> ProductSearchResponse:
    query = ProductQuery(
        keyword=q.strip() if q and q.strip() else None,
        category=category.strip() if category and category.strip() else None,
        price_min_cents=price_min_cents,
        price_max_cents=price_max_cents,
        min_commission_rate_bp=min_commission_rate_bp,
        sort=sort,
        page=page,
        page_size=page_size,
    )
    service = ProductService(session, providers.product)
    result, products = service.search(query)

    return ProductSearchResponse(
        items=[ProductOut.from_model(product) for product in products],
        page=result.page,
        page_size=result.page_size,
        has_next=result.has_next,
        total=result.total,
        source=providers.source,
        is_demo=providers.product.is_demo,
    )


@router.get("/categories", response_model=CategoriesResponse)
def list_categories(
    session: Session = Depends(get_db),
    providers: Providers = Depends(get_providers),
) -> CategoriesResponse:
    service = ProductService(session, providers.product)
    return CategoriesResponse(
        items=service.categories(),
        source=providers.source,
        is_demo=providers.product.is_demo,
    )
