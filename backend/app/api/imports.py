"""Endpoints de importação CSV e do histórico de importações."""

from typing import Literal

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.constants import MAX_PAGE_SIZE
from app.core.deps import get_db
from app.core.errors import NotFoundError
from app.repositories import imports as imports_repository
from app.schemas.imports import (
    ImportDetailOut,
    ImportedRowOut,
    ImportListResponse,
    ImportOut,
)
from app.services.csv_import import CsvImportService

router = APIRouter(prefix="/imports", tags=["imports"])

ReportType = Literal["orders", "clicks"]
ImportStatus = Literal["running", "completed", "partial", "failed"]
RowStatus = Literal["imported", "skipped", "error"]


@router.post("/orders", status_code=201, response_model=ImportOut)
async def import_orders(
    request: Request,
    filename: str = Query(default="conversion.csv", max_length=300),
    session: Session = Depends(get_db),
) -> ImportOut:
    content = await request.body()
    log = CsvImportService(session).import_orders(filename, content)
    return ImportOut.from_model(log)


@router.post("/clicks", status_code=201, response_model=ImportOut)
async def import_clicks(
    request: Request,
    filename: str = Query(default="clicks.csv", max_length=300),
    session: Session = Depends(get_db),
) -> ImportOut:
    content = await request.body()
    log = CsvImportService(session).import_clicks(filename, content)
    return ImportOut.from_model(log)


@router.get("", response_model=ImportListResponse)
def list_imports(
    report_type: ReportType | None = Query(default=None),
    import_status: ImportStatus | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=MAX_PAGE_SIZE),
    session: Session = Depends(get_db),
) -> ImportListResponse:
    items, total = imports_repository.list_page(
        session,
        report_type=report_type,
        status=import_status,
        page=page,
        page_size=page_size,
    )
    return ImportListResponse(
        items=[ImportOut.from_model(item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
        has_next=page * page_size < total,
    )


@router.get("/{import_id}", response_model=ImportDetailOut)
def get_import(
    import_id: int,
    row_status: RowStatus | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=MAX_PAGE_SIZE),
    session: Session = Depends(get_db),
) -> ImportDetailOut:
    log = imports_repository.get_by_id(session, import_id)
    if log is None:
        raise NotFoundError("Importação não encontrada.")

    rows, matching = imports_repository.list_rows(
        session,
        import_id,
        row_status=row_status,
        page=page,
        page_size=page_size,
    )
    summary = ImportOut.from_model(log)
    return ImportDetailOut(
        **summary.model_dump(),
        rows=[ImportedRowOut.from_model(row) for row in rows],
        rows_page=page,
        rows_page_size=page_size,
        rows_matching=matching,
        rows_has_next=page * page_size < matching,
    )
