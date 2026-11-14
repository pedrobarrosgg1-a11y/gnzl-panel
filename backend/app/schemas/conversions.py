"""Schemas da sincronização de conversões."""

from pydantic import BaseModel

from app.schemas.common import UtcDateTime
from app.schemas.imports import ImportOut
from app.services.conversion_sync import ConversionSyncResult


class ConversionSyncOut(BaseModel):
    window_start: UtcDateTime
    window_end: UtcDateTime
    total: int
    created: int
    updated: int
    skipped: int
    failed: int
    import_log: ImportOut

    @classmethod
    def from_result(cls, result: ConversionSyncResult) -> "ConversionSyncOut":
        return cls(
            window_start=result.window_start,
            window_end=result.window_end,
            total=result.total,
            created=result.created,
            updated=result.updated,
            skipped=result.skipped,
            failed=result.failed,
            import_log=ImportOut.from_model(result.log),
        )
