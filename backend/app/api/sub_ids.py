"""Endpoints de Sub IDs."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.schemas.sub_ids import (
    NormalizeResponse,
    SubIdDimension,
    SubIdListResponse,
    SubIdSuggestion,
)
from app.services.sub_ids import SubIdService

router = APIRouter(prefix="/sub-ids", tags=["sub ids"])


@router.get("", response_model=SubIdListResponse)
def suggestions(
    dimension: SubIdDimension = Query(...),
    q: str | None = Query(default=None, max_length=64),
    limit: int = Query(default=10, ge=1, le=50),
    session: Session = Depends(get_db),
) -> SubIdListResponse:
    service = SubIdService(session)
    return SubIdListResponse(
        items=[
            SubIdSuggestion.from_model(value)
            for value in service.suggestions(dimension, q, limit)
        ]
    )


@router.get("/normalize", response_model=NormalizeResponse)
def normalize(
    dimension: SubIdDimension = Query(...),
    value: str = Query(..., max_length=200),
    session: Session = Depends(get_db),
) -> NormalizeResponse:
    service = SubIdService(session)
    return NormalizeResponse(
        normalized=service.normalize_preview(dimension, value),
        dimension=dimension,
    )
