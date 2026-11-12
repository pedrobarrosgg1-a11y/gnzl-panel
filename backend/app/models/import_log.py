"""Importações de relatórios e resultado linha a linha.

``import_logs`` guarda o cabeçalho da operação (arquivo, tipo de relatório,
contadores e status). ``imported_rows`` guarda o destino de cada linha, para
auditar importações parciais sem esconder linhas ignoradas ou com erro.

As linhas não são apagadas quando um pedido ou clique é removido: o vínculo cai
para ``NULL`` e o registro da importação permanece como histórico.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utcnow
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.conversion import Click, Order

REPORT_TYPES = ("orders", "clicks")
IMPORT_STATUSES = ("running", "completed", "partial", "failed")
IMPORTED_ROW_STATUSES = ("imported", "skipped", "error")


class ImportLog(Base):
    """Uma execução de importação de relatório CSV."""

    __tablename__ = "import_logs"
    __table_args__ = (
        CheckConstraint("report_type IN ('orders', 'clicks')", name="report_type"),
        CheckConstraint(
            "status IN ('running', 'completed', 'partial', 'failed')", name="status"
        ),
        CheckConstraint("data_source IN ('demo', 'shopee', 'csv')", name="data_source"),
        CheckConstraint(
            "rows_total >= 0 AND rows_imported >= 0 "
            "AND rows_skipped >= 0 AND rows_failed >= 0",
            name="rows_non_negative",
        ),
        CheckConstraint(
            "rows_imported + rows_skipped + rows_failed <= rows_total",
            name="rows_consistency",
        ),
        Index("ix_import_logs_created_at", "created_at"),
        Index("ix_import_logs_report_type", "report_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String(300), nullable=False)
    report_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running")
    data_source: Mapped[str] = mapped_column(String(20), nullable=False, default="csv")
    rows_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rows_imported: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rows_skipped: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rows_failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)

    rows: Mapped[list["ImportedRow"]] = relationship(
        back_populates="import_log",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ImportedRow.row_number",
    )


class ImportedRow(Base):
    """Resultado de uma linha do arquivo, inclusive quando ignorada ou inválida."""

    __tablename__ = "imported_rows"
    __table_args__ = (
        UniqueConstraint(
            "import_id", "row_number", name="uq_imported_rows_import_row"
        ),
        CheckConstraint("row_number > 0", name="row_number_positive"),
        CheckConstraint(
            "status IN ('imported', 'skipped', 'error')", name="status"
        ),
        # Uma linha produz no máximo um registro de domínio.
        CheckConstraint(
            "order_id IS NULL OR click_id IS NULL", name="single_reference"
        ),
        Index("ix_imported_rows_import_status", "import_id", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    import_id: Mapped[int] = mapped_column(
        ForeignKey("import_logs.id", ondelete="CASCADE"), nullable=False
    )
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="imported")
    order_id: Mapped[int | None] = mapped_column(
        ForeignKey("orders.id", ondelete="SET NULL")
    )
    click_id: Mapped[int | None] = mapped_column(
        ForeignKey("clicks.id", ondelete="SET NULL")
    )
    message: Mapped[str | None] = mapped_column(Text)
    raw_data: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    import_log: Mapped[ImportLog] = relationship(back_populates="rows")
    order: Mapped["Order | None"] = relationship()
    click: Mapped["Click | None"] = relationship()
