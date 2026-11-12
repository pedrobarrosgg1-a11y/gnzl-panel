"""Schemas das importações CSV."""

import json

from pydantic import BaseModel

from app.models.import_log import ImportedRow, ImportLog
from app.schemas.common import UtcDateTime


class ImportedRowOut(BaseModel):
    id: int
    row_number: int
    status: str
    message: str | None
    order_id: int | None
    click_id: int | None
    raw_data: dict[str, str] | None

    @classmethod
    def from_model(cls, row: ImportedRow) -> "ImportedRowOut":
        return cls(
            id=row.id,
            row_number=row.row_number,
            status=row.status,
            message=row.message,
            order_id=row.order_id,
            click_id=row.click_id,
            raw_data=_parse_raw(row.raw_data),
        )


class ImportOut(BaseModel):
    id: int
    filename: str
    report_type: str
    status: str
    source: str
    is_demo: bool
    rows_total: int
    rows_imported: int
    rows_skipped: int
    rows_failed: int
    error_message: str | None
    created_at: UtcDateTime
    finished_at: UtcDateTime | None

    @classmethod
    def from_model(cls, log: ImportLog) -> "ImportOut":
        return cls(
            id=log.id,
            filename=log.filename,
            report_type=log.report_type,
            status=log.status,
            source=log.data_source,
            is_demo=log.data_source == "demo",
            rows_total=log.rows_total,
            rows_imported=log.rows_imported,
            rows_skipped=log.rows_skipped,
            rows_failed=log.rows_failed,
            error_message=log.error_message,
            created_at=log.created_at,
            finished_at=log.finished_at,
        )


class ImportListResponse(BaseModel):
    items: list[ImportOut]
    page: int
    page_size: int
    total: int
    has_next: bool


class ImportDetailOut(ImportOut):
    rows: list[ImportedRowOut]
    rows_page: int
    rows_page_size: int
    rows_matching: int
    rows_has_next: bool


def _parse_raw(raw_data: str | None) -> dict[str, str] | None:
    if not raw_data:
        return None
    try:
        parsed = json.loads(raw_data)
    except ValueError:
        return None
    return parsed if isinstance(parsed, dict) else None
