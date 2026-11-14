"""Endpoint de sincronização de conversões da fonte oficial."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.constants import MAX_CONVERSION_WINDOW_DAYS
from app.core.deps import get_db, get_providers
from app.core.errors import ProviderNotSupported
from app.providers.registry import Providers
from app.schemas.conversions import ConversionSyncOut
from app.services.conversion_sync import ConversionSyncService

router = APIRouter(prefix="/conversions", tags=["conversions"])


@router.post("/sync", status_code=201, response_model=ConversionSyncOut)
def sync_conversions(
    days: int = Query(default=30, ge=1, le=MAX_CONVERSION_WINDOW_DAYS),
    session: Session = Depends(get_db),
    providers: Providers = Depends(get_providers),
) -> ConversionSyncOut:
    provider = providers.conversions
    if provider is None:
        raise ProviderNotSupported(
            "A sincronização de conversões exige GNZL_PROVIDER=shopee."
        )

    result = ConversionSyncService(session, provider).sync(days)
    return ConversionSyncOut.from_result(result)
