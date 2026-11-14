"""Importação de relatórios CSV.

O contrato canônico é definido aqui, não pelas colunas da Shopee. O adaptador
do relatório real (etapa futura) converte o arquivo oficial para este formato.
Nenhum nome de coluna da Shopee é presumido.

Arquivo de pedidos (``orders``)::

    order_id,item_id,shop_id,status,status_group,ordered_at,completed_at,
    quantity,sales_cents,commission_cents,sub_id_1..sub_id_5,channel,title,
    image_url

Obrigatórias: ``order_id``, ``item_id``, ``status`` e ``ordered_at``.
``status_group`` ausente é derivado de ``status`` pelas mesmas regras do
provedor oficial; quando presente, precisa ser um grupo válido.

Arquivo de cliques (``clicks``)::

    click_id,clicked_at,region,channel,referrer,sub_id_1..sub_id_5

Obrigatórias: ``click_id`` e ``clicked_at``.

Formatos aceitos: UTF-8 (com ou sem BOM), Windows-1252 como alternativa,
separador ``,`` ou ``;``. Datas em ISO-8601 ou ``DD/MM/AAAA HH:MM[:SS]``.
Valores monetários já em centavos, como no restante do banco.
"""

import csv
import hashlib
import io
import json
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.constants import MAX_IMPORT_BYTES
from app.core.conversion_rules import (
    DEFAULT_QUANTITY,
    MAX_ORDER_ID_LENGTH,
    MAX_STATUS_LENGTH,
    MAX_TITLE_LENGTH,
    STATUS_GROUPS,
    normalize_channel,
    status_group_from_raw,
    truncate_text,
)
from app.core.errors import ValidationError
from app.core.time import utcnow
from app.models.conversion import Click, Order
from app.models.import_log import ImportLog, ImportedRow
from app.repositories import imports as imports_repository
from app.services.normalization import normalize_sub_id_slots

DATA_SOURCE = "csv"

ORDER_REQUIRED = ("order_id", "item_id", "status", "ordered_at")
ORDER_OPTIONAL = (
    "shop_id",
    "status_group",
    "completed_at",
    "quantity",
    "sales_cents",
    "commission_cents",
    "sub_id_1",
    "sub_id_2",
    "sub_id_3",
    "sub_id_4",
    "sub_id_5",
    "channel",
    "title",
    "image_url",
)
ORDER_COLUMNS = ORDER_REQUIRED + ORDER_OPTIONAL

CLICK_REQUIRED = ("click_id", "clicked_at")
CLICK_OPTIONAL = (
    "region",
    "channel",
    "referrer",
    "sub_id_1",
    "sub_id_2",
    "sub_id_3",
    "sub_id_4",
    "sub_id_5",
)
CLICK_COLUMNS = CLICK_REQUIRED + CLICK_OPTIONAL

_BRAZILIAN_DATETIME_FORMATS = (
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y %H:%M",
    "%d/%m/%Y",
)

MAX_MESSAGE_LENGTH = 500
MAX_RAW_DATA_LENGTH = 4000


class RowError(ValueError):
    """Falha de uma linha. Não interrompe as demais linhas do arquivo."""


@dataclass(frozen=True)
class ParsedRow:
    row_number: int
    values: dict[str, str]


@dataclass(frozen=True)
class RejectedRow:
    row_number: int
    message: str
    raw: dict[str, str]


@dataclass(frozen=True)
class ParseResult:
    rows: list[ParsedRow]
    rejected: list[RejectedRow]
    total: int


@dataclass(frozen=True)
class OrderPayload:
    row_number: int
    dedup_key: str
    external_order_id: str
    external_item_id: int
    shop_id: int | None
    status: str
    status_group: str
    ordered_at: datetime
    completed_at: datetime | None
    quantity: int
    sales_cents: int
    commission_cents: int
    sub_ids: tuple[str | None, ...]
    channel: str | None
    title: str | None
    image_url: str | None
    raw: dict[str, str]

    def to_model(self) -> Order:
        return Order(
            external_order_id=self.external_order_id,
            external_item_id=self.external_item_id,
            shop_id=self.shop_id,
            status=self.status,
            status_group=self.status_group,
            ordered_at=self.ordered_at,
            completed_at=self.completed_at,
            quantity=self.quantity,
            sales_cents=self.sales_cents,
            commission_cents=self.commission_cents,
            sub_id_1=self.sub_ids[0],
            sub_id_2=self.sub_ids[1],
            sub_id_3=self.sub_ids[2],
            sub_id_4=self.sub_ids[3],
            sub_id_5=self.sub_ids[4],
            channel=self.channel,
            title=self.title,
            image_url=self.image_url,
            data_source=DATA_SOURCE,
            dedup_key=self.dedup_key,
        )


@dataclass(frozen=True)
class ClickPayload:
    row_number: int
    dedup_key: str
    external_click_id: str
    clicked_at: datetime
    region: str | None
    channel: str | None
    referrer: str | None
    sub_ids: tuple[str | None, ...]
    raw: dict[str, str]

    def to_model(self) -> Click:
        return Click(
            external_click_id=self.external_click_id,
            clicked_at=self.clicked_at,
            region=self.region,
            channel=self.channel,
            referrer=self.referrer,
            sub_id_1=self.sub_ids[0],
            sub_id_2=self.sub_ids[1],
            sub_id_3=self.sub_ids[2],
            sub_id_4=self.sub_ids[3],
            sub_id_5=self.sub_ids[4],
            data_source=DATA_SOURCE,
            dedup_key=self.dedup_key,
        )


def parse_report(
    content: bytes,
    *,
    required: tuple[str, ...],
    optional: tuple[str, ...],
) -> ParseResult:
    """Lê o arquivo e separa linhas válidas de linhas rejeitadas.

    Problemas estruturais (arquivo vazio, cabeçalho ausente, coluna
    obrigatória faltando) interrompem a importação. Problemas de linha são
    registrados e não impedem as demais.
    """
    text = _decode(content)
    delimiter = _delimiter(text)
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=delimiter)

    try:
        header = next(reader)
    except StopIteration as exc:
        raise ValidationError("O arquivo não tem conteúdo.") from exc

    columns = [column.strip().lstrip("\ufeff") for column in header]
    if not any(columns):
        raise ValidationError("O arquivo não tem cabeçalho.")
    if len(set(columns)) != len(columns):
        raise ValidationError("O cabeçalho tem colunas repetidas.")

    missing = [column for column in required if column not in columns]
    if missing:
        raise ValidationError(
            f"Faltam colunas obrigatórias: {', '.join(missing)}.",
            details={
                "missing_columns": missing,
                "required_columns": list(required),
                "accepted_columns": [*required, *optional],
            },
        )

    positions = {column: index for index, column in enumerate(columns)}
    rows: list[ParsedRow] = []
    rejected: list[RejectedRow] = []
    total = 0

    for row_number, values in enumerate(reader, start=2):
        if not any(cell.strip() for cell in values):
            continue
        total += 1
        raw = {
            column: values[index].strip() if index < len(values) else ""
            for column, index in positions.items()
        }
        if len(values) > len(columns):
            rejected.append(
                RejectedRow(
                    row_number,
                    "A linha tem mais colunas que o cabeçalho.",
                    raw,
                )
            )
            continue
        empty_required = [
            column for column in required if not raw.get(column, "").strip()
        ]
        if empty_required:
            rejected.append(
                RejectedRow(
                    row_number,
                    f"Campos obrigatórios vazios: {', '.join(empty_required)}.",
                    raw,
                )
            )
            continue
        rows.append(ParsedRow(row_number=row_number, values=raw))

    return ParseResult(rows=rows, rejected=rejected, total=total)


class CsvImportService:
    """Importa pedidos e cliques de um CSV canônico."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def import_orders(self, filename: str, content: bytes) -> ImportLog:
        parsed = self._parse(content, required=ORDER_REQUIRED, optional=ORDER_OPTIONAL)
        payloads: list[OrderPayload] = []
        rejected = list(parsed.rejected)
        for row in parsed.rows:
            try:
                payloads.append(_build_order(row))
            except RowError as exc:
                rejected.append(RejectedRow(row.row_number, str(exc), row.values))

        existing = imports_repository.existing_order_ids(
            self._session, {payload.dedup_key for payload in payloads}
        )
        log = self._new_log("orders", filename, parsed.total)
        created: dict[str, Order] = {}
        imported = skipped = 0

        for payload in payloads:
            if payload.dedup_key in existing:
                skipped += 1
                log.rows.append(
                    _row(
                        payload.row_number,
                        "skipped",
                        "Linha já importada anteriormente.",
                        payload.raw,
                        order_id=existing[payload.dedup_key],
                    )
                )
            elif payload.dedup_key in created:
                skipped += 1
                log.rows.append(
                    _row(
                        payload.row_number,
                        "skipped",
                        "Linha repetida no mesmo arquivo.",
                        payload.raw,
                        order=created[payload.dedup_key],
                    )
                )
            else:
                order = payload.to_model()
                order.import_id = log.id
                self._session.add(order)
                created[payload.dedup_key] = order
                imported += 1
                log.rows.append(
                    _row(payload.row_number, "imported", None, payload.raw, order=order)
                )

        for item in rejected:
            log.rows.append(
                _row(item.row_number, "error", item.message, item.raw)
            )

        self._finish(log, imported=imported, skipped=skipped, failed=len(rejected))
        return log

    def import_clicks(self, filename: str, content: bytes) -> ImportLog:
        parsed = self._parse(content, required=CLICK_REQUIRED, optional=CLICK_OPTIONAL)
        payloads: list[ClickPayload] = []
        rejected = list(parsed.rejected)
        for row in parsed.rows:
            try:
                payloads.append(_build_click(row))
            except RowError as exc:
                rejected.append(RejectedRow(row.row_number, str(exc), row.values))

        existing = imports_repository.existing_click_ids(
            self._session, {payload.dedup_key for payload in payloads}
        )
        log = self._new_log("clicks", filename, parsed.total)
        created: dict[str, Click] = {}
        imported = skipped = 0

        for payload in payloads:
            if payload.dedup_key in existing:
                skipped += 1
                log.rows.append(
                    _row(
                        payload.row_number,
                        "skipped",
                        "Linha já importada anteriormente.",
                        payload.raw,
                        click_id=existing[payload.dedup_key],
                    )
                )
            elif payload.dedup_key in created:
                skipped += 1
                log.rows.append(
                    _row(
                        payload.row_number,
                        "skipped",
                        "Linha repetida no mesmo arquivo.",
                        payload.raw,
                        click=created[payload.dedup_key],
                    )
                )
            else:
                click = payload.to_model()
                click.import_id = log.id
                self._session.add(click)
                created[payload.dedup_key] = click
                imported += 1
                log.rows.append(
                    _row(payload.row_number, "imported", None, payload.raw, click=click)
                )

        for item in rejected:
            log.rows.append(
                _row(item.row_number, "error", item.message, item.raw)
            )

        self._finish(log, imported=imported, skipped=skipped, failed=len(rejected))
        return log

    def _parse(
        self,
        content: bytes,
        *,
        required: tuple[str, ...],
        optional: tuple[str, ...],
    ) -> ParseResult:
        parsed = parse_report(content, required=required, optional=optional)
        if parsed.total == 0:
            raise ValidationError("O arquivo não tem linhas de dados.")
        return parsed

    def _new_log(self, report_type: str, filename: str, rows_total: int) -> ImportLog:
        log = ImportLog(
            filename=_normalize_filename(filename),
            report_type=report_type,
            data_source=DATA_SOURCE,
            rows_total=rows_total,
        )
        self._session.add(log)
        # Necessário para vincular as linhas antes de encerrar a transação.
        self._session.flush()
        return log

    def _finish(
        self,
        log: ImportLog,
        *,
        imported: int,
        skipped: int,
        failed: int,
    ) -> None:
        log.rows_imported = imported
        log.rows_skipped = skipped
        log.rows_failed = failed
        log.status = _final_status(imported, skipped, failed)
        log.finished_at = utcnow()
        self._session.commit()


def _decode(content: bytes) -> str:
    if not content:
        raise ValidationError("O arquivo enviado está vazio.")
    if len(content) > MAX_IMPORT_BYTES:
        raise ValidationError(
            "O arquivo excede o limite de 10 MB.",
            details={"max_bytes": MAX_IMPORT_BYTES},
        )
    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            return content.decode("cp1252")
        except UnicodeDecodeError as exc:
            raise ValidationError(
                "O arquivo precisa estar em UTF-8 ou Windows-1252."
            ) from exc


def _delimiter(text: str) -> str:
    """Aceita vírgula e ponto e vírgula sem exigir configuração."""
    first_line = next((line for line in text.splitlines() if line.strip()), "")
    return ";" if ";" in first_line and "," not in first_line else ","


def _build_order(row: ParsedRow) -> OrderPayload:
    raw = row.values
    external_order_id = _required_text(
        raw, "order_id", max_length=MAX_ORDER_ID_LENGTH
    )
    external_item_id = _required_integer(raw, "item_id")
    ordered_at = _required_datetime(raw, "ordered_at")
    status = (
        truncate_text(_required_text(raw, "status"), MAX_STATUS_LENGTH) or "unknown"
    )

    return OrderPayload(
        row_number=row.row_number,
        dedup_key=_dedup_key("order", external_order_id, str(external_item_id)),
        external_order_id=external_order_id,
        external_item_id=external_item_id,
        shop_id=_optional_integer(raw, "shop_id"),
        status=status,
        status_group=_status_group(raw.get("status_group"), status),
        ordered_at=ordered_at,
        completed_at=_optional_datetime(raw, "completed_at"),
        quantity=_integer_value(
            raw, "quantity", default=DEFAULT_QUANTITY, minimum=0
        ),
        sales_cents=_integer_value(raw, "sales_cents", default=0, minimum=0),
        commission_cents=_integer_value(
            raw, "commission_cents", default=0, minimum=0
        ),
        sub_ids=_sub_ids(raw),
        channel=normalize_channel(raw.get("channel")),
        title=truncate_text(_optional_text(raw, "title"), MAX_TITLE_LENGTH),
        image_url=_optional_text(raw, "image_url"),
        raw=raw,
    )


def _build_click(row: ParsedRow) -> ClickPayload:
    raw = row.values
    external_click_id = _required_text(raw, "click_id", max_length=120)

    return ClickPayload(
        row_number=row.row_number,
        dedup_key=_dedup_key("click", external_click_id),
        external_click_id=external_click_id,
        clicked_at=_required_datetime(raw, "clicked_at"),
        region=_optional_text(raw, "region", max_length=80),
        channel=normalize_channel(raw.get("channel")),
        referrer=_optional_text(raw, "referrer"),
        sub_ids=_sub_ids(raw),
        raw=raw,
    )


def _required_text(
    raw: dict[str, str], field: str, *, max_length: int | None = None
) -> str:
    value = (raw.get(field) or "").strip()
    if not value:
        raise RowError(f"{field} está vazio.")
    return _check_length(value, field, max_length)


def _optional_text(
    raw: dict[str, str], field: str, *, max_length: int | None = None
) -> str | None:
    value = (raw.get(field) or "").strip()
    if not value:
        return None
    return _check_length(value, field, max_length)


def _check_length(value: str, field: str, max_length: int | None) -> str:
    if max_length is not None and len(value) > max_length:
        raise RowError(f"{field} excede {max_length} caracteres.")
    return value


def _required_integer(raw: dict[str, str], field: str) -> int:
    value = (raw.get(field) or "").strip()
    if not value:
        raise RowError(f"{field} está vazio.")
    return _parse_integer(value, field)


def _optional_integer(raw: dict[str, str], field: str) -> int | None:
    value = (raw.get(field) or "").strip()
    if not value:
        return None
    return _parse_integer(value, field)


def _integer_value(
    raw: dict[str, str],
    field: str,
    *,
    default: int,
    minimum: int | None = None,
) -> int:
    value = (raw.get(field) or "").strip()
    if not value:
        return default
    number = _parse_integer(value, field)
    if minimum is not None and number < minimum:
        raise RowError(f"{field} não pode ser menor que {minimum}.")
    return number


def _parse_integer(value: str, field: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise RowError(f"{field} precisa ser um número inteiro.") from exc


def _required_datetime(raw: dict[str, str], field: str) -> datetime:
    value = (raw.get(field) or "").strip()
    if not value:
        raise RowError(f"{field} está vazio.")
    return _parse_datetime(value, field)


def _optional_datetime(raw: dict[str, str], field: str) -> datetime | None:
    value = (raw.get(field) or "").strip()
    if not value:
        return None
    return _parse_datetime(value, field)


def _parse_datetime(value: str, field: str) -> datetime:
    candidate = f"{value[:-1]}+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        parsed = _parse_brazilian_datetime(value, field)

    if parsed.tzinfo is not None:
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def _parse_brazilian_datetime(value: str, field: str) -> datetime:
    for pattern in _BRAZILIAN_DATETIME_FORMATS:
        try:
            return datetime.strptime(value, pattern)
        except ValueError:
            continue
    raise RowError(f"{field} precisa estar em ISO-8601 ou DD/MM/AAAA HH:MM.")


def _status_group(value: str | None, status: str) -> str:
    """Usa o grupo declarado no arquivo; sem ele, classifica o status bruto.

    O grupo declarado é uma afirmação explícita de quem gerou o relatório e
    prevalece. Se estiver inválido, a linha é rejeitada em vez de adivinhar:
    um valor errado distorceria as métricas sem deixar rastro.
    """
    group = (value or "").strip().lower()
    if not group:
        return status_group_from_raw(status)
    if group not in STATUS_GROUPS:
        raise RowError(
            "status_group inválido. Use "
            + ", ".join(STATUS_GROUPS)
            + "."
        )
    return group


def _sub_ids(raw: dict[str, str]) -> tuple[str | None, ...]:
    try:
        return normalize_sub_id_slots(
            [raw.get(f"sub_id_{index}") for index in range(1, 6)]
        )
    except ValidationError as exc:
        raise RowError(exc.message) from exc


def _dedup_key(prefix: str, *parts: str) -> str:
    """Chave determinística e curta para a restrição única por origem."""
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return f"{prefix}:{digest}"


def _normalize_filename(filename: str) -> str:
    name = filename.replace("\\", "/").rsplit("/", 1)[-1].strip()
    name = "".join(character for character in name if character.isprintable())
    return (name or "relatorio.csv")[:300]


def _row(
    row_number: int,
    status: str,
    message: str | None,
    raw: dict[str, str],
    *,
    order: Order | None = None,
    order_id: int | None = None,
    click: Click | None = None,
    click_id: int | None = None,
) -> ImportedRow:
    values: dict[str, object] = {
        "row_number": row_number,
        "status": status,
        "message": _short(message),
        "raw_data": _dump_raw(raw),
    }
    # Passar `order=None` junto de `order_id` pode zerar a FK no flush; só
    # enviamos o vínculo que existe.
    if order is not None:
        values["order"] = order
    elif order_id is not None:
        values["order_id"] = order_id
    if click is not None:
        values["click"] = click
    elif click_id is not None:
        values["click_id"] = click_id
    return ImportedRow(**values)


def _short(message: str | None) -> str | None:
    if message is None:
        return None
    return message[:MAX_MESSAGE_LENGTH]


def _dump_raw(raw: dict[str, str]) -> str | None:
    try:
        dumped = json.dumps(raw, ensure_ascii=False)
    except (TypeError, ValueError):
        return None
    return dumped[:MAX_RAW_DATA_LENGTH]


def _final_status(imported: int, skipped: int, failed: int) -> str:
    if failed == 0:
        return "completed"
    if imported + skipped > 0:
        return "partial"
    return "failed"
