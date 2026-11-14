"""Utilitários de tempo.

Toda data/hora é gravada em UTC sem timezone (SQLite não guarda tzinfo).
A conversão para o horário local acontece na apresentação e nos recortes por
período, como o do dashboard.

O Brasil não tem horário de verão desde 2019: o fuso de São Paulo é UTC-3 o ano
inteiro. Usar um offset fixo evita depender de ``tzdata``, que não vem instalado
no Windows por padrão.
"""

from datetime import date, datetime, time, timedelta, timezone

LOCAL_UTC_OFFSET_HOURS = -3


def utcnow() -> datetime:
    """Agora, em UTC, sem tzinfo — formato consistente com o que o SQLite devolve."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def local_today(now: datetime | None = None) -> date:
    """Data de hoje no horário de Brasília, independente do fuso da máquina."""
    reference = now or utcnow()
    if reference.tzinfo is not None:
        reference = reference.astimezone(timezone.utc).replace(tzinfo=None)
    return (reference + timedelta(hours=LOCAL_UTC_OFFSET_HOURS)).date()


def local_day_start_utc(day: date) -> datetime:
    """Instante UTC (sem tzinfo) em que o dia local começa."""
    return datetime.combine(day, time.min) - timedelta(hours=LOCAL_UTC_OFFSET_HOURS)


def local_day_end_utc(day: date) -> datetime:
    """Instante UTC em que o dia local termina — início do dia seguinte.

    É um limite **exclusivo**: ``start <= x < end`` não depende de precisão de
    microssegundos no último instante do dia.
    """
    return local_day_start_utc(day + timedelta(days=1))
