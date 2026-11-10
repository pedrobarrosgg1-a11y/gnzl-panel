"""Endpoints de sistema: saúde e configuração pública."""

from fastapi import APIRouter, Depends

from app import __version__
from app.core.config import Settings, get_settings
from app.schemas.system import ConfigResponse, HealthResponse

router = APIRouter(tags=["sistema"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", version=__version__)


@router.get("/config", response_model=ConfigResponse)
def config(settings: Settings = Depends(get_settings)) -> ConfigResponse:
    return ConfigResponse(
        version=__version__,
        environment=settings.environment,
        provider=settings.provider,
        is_demo=settings.is_demo,
    )
