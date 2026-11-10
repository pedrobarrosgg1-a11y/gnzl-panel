"""Utilitários de tempo.

Toda data/hora é gravada em UTC sem timezone (SQLite não guarda tzinfo).
A conversão para o horário local acontece na apresentação.
"""

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Agora, em UTC, sem tzinfo — formato consistente com o que o SQLite devolve."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
