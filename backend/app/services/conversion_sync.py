"""Sincronização de conversões da fonte oficial.

A chamada externa acontece antes de qualquer escrita. Se o provedor falhar,
nada é gravado: não existe importação pela metade nem log ``running`` eterno.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.errors import ValidationError
from app.core.time import utcnow
from app.models.conversion import Order
from app.models.import_log import ImportedRow, ImportLog
from app.providers.base import ConversionProvider, ConversionQuery, ConversionRecord
from app.repositories import conversions as conversions_repository

MAX_MESSAGE_LENGTH = 500
MAX_RAW_DATA_LENGTH = 4000

# Campos que uma nova leitura da fonte pode corrigir. A identidade do registro
# (pedido + item + variante) vive no dedup_key e não muda.
_MUTABLE_FIELDS = (
    "external_item_id",
    "shop_id",
    "title",
    "image_url",
    "status",
    "status_group",
    "ordered_at",
    "completed_at",
    "quantity",
    "sales_cents",
    "commission_cents",
    "channel",
)


@dataclass(frozen=True)
class ConversionSyncResult:
    log: ImportLog
    window_start: datetime
    window_end: datetime
    total: int
    created: int
    updated: int
    skipped: int
    failed: int


class ConversionSyncService:
    """Persiste o relatório da fonte e atualiza o que mudou desde a última vez."""

    def __init__(
        self,
        session: Session,
        provider: ConversionProvider,
        *,
        now=utcnow,
    ) -> None:
        self._session = session
        self._provider = provider
        self._now = now

    def sync(self, days: int) -> ConversionSyncResult:
        window = self._window(days)
        records = self._provider.fetch_conversions(window)

        log = self._start_log(window, total=len(records))
        existing = conversions_repository.existing_orders(
            self._session,
            data_source=self._provider.name,
            dedup_keys={record.dedup_key for record in records},
        )
        created: dict[str, Order] = {}
        created_count = updated_count = skipped_count = 0

        for row_number, record in enumerate(records, start=1):
            if record.dedup_key in existing:
                order = existing[record.dedup_key]
                if _apply(record, order):
                    updated_count += 1
                    self._append_row(
                        log,
                        row_number,
                        "imported",
                        "Pedido atualizado com os dados mais recentes.",
                        record,
                        order,
                    )
                else:
                    skipped_count += 1
                    self._append_row(
                        log,
                        row_number,
                        "skipped",
                        "Pedido já sincronizado; nada mudou.",
                        record,
                        order,
                    )
            elif record.dedup_key in created:
                skipped_count += 1
                self._append_row(
                    log,
                    row_number,
                    "skipped",
                    "Registro repetido na mesma sincronização.",
                    record,
                    created[record.dedup_key],
                )
            else:
                order = _to_model(
                    record,
                    data_source=self._provider.name,
                    import_id=log.id,
                )
                self._session.add(order)
                created[record.dedup_key] = order
                created_count += 1
                self._append_row(
                    log,
                    row_number,
                    "imported",
                    "Pedido criado.",
                    record,
                    order,
                )

        self._finish(
            log,
            created=created_count,
            updated=updated_count,
            skipped=skipped_count,
        )
        return ConversionSyncResult(
            log=log,
            window_start=window.start,
            window_end=window.end,
            total=len(records),
            created=created_count,
            updated=updated_count,
            skipped=skipped_count,
            failed=0,
        )

    def _window(self, days: int) -> ConversionQuery:
        maximum = self._provider.conversion_window_days
        if not 1 <= days <= maximum:
            raise ValidationError(
                f"A janela de sincronização deve ter entre 1 e {maximum} dias.",
                details={"days": days, "max_days": maximum},
            )
        end = _as_naive_utc(self._now())
        return ConversionQuery(start=end - timedelta(days=days), end=end)

    def _start_log(
        self, window: ConversionQuery, *, total: int
    ) -> ImportLog:
        log = ImportLog(
            filename=_filename(
                self._provider.name, window.start, window.end
            ),
            report_type="orders",
            data_source=self._provider.name,
            rows_total=total,
        )
        self._session.add(log)
        # Necessário para vincular as linhas antes de encerrar a transação.
        self._session.flush()
        return log

    def _append_row(
        self,
        log: ImportLog,
        row_number: int,
        status: str,
        message: str,
        record: ConversionRecord,
        order: Order,
    ) -> None:
        log.rows.append(
            ImportedRow(
                row_number=row_number,
                status=status,
                message=_short(message),
                raw_data=_dump_raw(record.raw),
                order=order,
            )
        )

    def _finish(
        self,
        log: ImportLog,
        *,
        created: int,
        updated: int,
        skipped: int,
    ) -> None:
        # ``imported`` significa "dados aplicados": criados + atualizados.
        # Atualizações não são registros novos, mas o histórico precisa mostrar
        # que a linha foi trazida de novo e alterou o pedido.
        log.rows_imported = created + updated
        log.rows_skipped = skipped
        log.rows_failed = 0
        log.status = "completed"
        log.finished_at = self._now()
        self._session.commit()


def _apply(record: ConversionRecord, order: Order) -> bool:
    """Copia os campos mutáveis e informa se algo realmente mudou."""
    changed = False
    for field in _MUTABLE_FIELDS:
        value = getattr(record, field)
        if getattr(order, field) != value:
            setattr(order, field, value)
            changed = True

    for index, sub_id in enumerate(_sub_id_slots(record.sub_ids), start=1):
        field = f"sub_id_{index}"
        if getattr(order, field) != sub_id:
            setattr(order, field, sub_id)
            changed = True
    return changed


def _to_model(
    record: ConversionRecord,
    *,
    data_source: str,
    import_id: int,
) -> Order:
    slots = _sub_id_slots(record.sub_ids)
    return Order(
        external_order_id=record.external_order_id,
        external_item_id=record.external_item_id,
        shop_id=record.shop_id,
        title=record.title,
        image_url=record.image_url,
        status=record.status,
        status_group=record.status_group,
        ordered_at=record.ordered_at,
        completed_at=record.completed_at,
        quantity=record.quantity,
        sales_cents=record.sales_cents,
        commission_cents=record.commission_cents,
        sub_id_1=slots[0],
        sub_id_2=slots[1],
        sub_id_3=slots[2],
        sub_id_4=slots[3],
        sub_id_5=slots[4],
        channel=record.channel,
        data_source=data_source,
        import_id=import_id,
        dedup_key=record.dedup_key,
    )


def _sub_id_slots(values: tuple[str | None, ...]) -> tuple[str | None, ...]:
    slots = tuple(values[:5])
    return slots + (None,) * (5 - len(slots))


def _filename(source: str, start: datetime, end: datetime) -> str:
    return f"{source}:conversion-report:{start:%Y-%m-%d}:{end:%Y-%m-%d}"[:300]


def _short(message: str | None) -> str | None:
    if message is None:
        return None
    return message[:MAX_MESSAGE_LENGTH]


def _dump_raw(raw: dict[str, Any]) -> str | None:
    # O teto evita textos gigantes no SQLite. Um JSON truncado deixa de ser
    # parseável e a leitura devolve ``None`` em vez de inventar estrutura.
    try:
        dumped = json.dumps(raw, ensure_ascii=False)
    except (TypeError, ValueError):
        return None
    return dumped[:MAX_RAW_DATA_LENGTH]


def _as_naive_utc(value: datetime) -> datetime:
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value
