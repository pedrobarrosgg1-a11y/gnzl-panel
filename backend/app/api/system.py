"""Endpoints de sistema: saúde e configuração pública."""

from fastapi import APIRouter, Depends

from app import __version__
from app.core.config import Settings, get_settings
from app.core.deps import get_providers
from app.providers.registry import Providers
from app.schemas.system import (
    CapabilitiesResponse,
    ConfigResponse,
    HealthResponse,
)

router = APIRouter(tags=["sistema"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", version=__version__)


@router.get("/config", response_model=ConfigResponse)
def config(
    settings: Settings = Depends(get_settings),
    providers: Providers = Depends(get_providers),
) -> ConfigResponse:
    capabilities = providers.capabilities
    return ConfigResponse(
        version=__version__,
        environment=settings.environment,
        provider=settings.provider,
        is_demo=settings.is_demo,
        capabilities=CapabilitiesResponse(
            category_filter=capabilities.category_filter,
            price_filter=capabilities.price_filter,
            commission_filter=capabilities.commission_filter,
            conversion_sync=capabilities.conversion_sync,
            conversion_window_days=capabilities.conversion_window_days,
            sorts=list(capabilities.sorts),
        ),
    )
