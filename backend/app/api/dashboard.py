"""Endpoint de métricas do dashboard."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.schemas.dashboard import DashboardOut, DashboardSource
from app.services.dashboard import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardOut)
def get_dashboard(
    source: DashboardSource = Query(
        description="Origem dos dados: demo, shopee ou csv."
    ),
    start: date | None = Query(default=None, description="Primeiro dia local."),
    end: date | None = Query(default=None, description="Último dia local."),
    session: Session = Depends(get_db),
) -> DashboardOut:
    report = DashboardService(session).report(source, start, end)
    return DashboardOut.from_report(report)
