"""Testes dos utilitários de tempo local."""

from datetime import date, datetime

from app.core.time import (
    local_day_end_utc,
    local_day_start_utc,
    local_today,
)


def test_local_today_handles_the_utc_midnight_boundary() -> None:
    assert local_today(datetime(2026, 11, 14, 2, 59)) == date(2026, 11, 13)
    assert local_today(datetime(2026, 11, 14, 3, 0)) == date(2026, 11, 14)


def test_local_today_accepts_an_aware_datetime() -> None:
    # 01:00Z = 22:00 do dia anterior em Brasília.
    aware = datetime.fromisoformat("2026-11-14T01:00:00+00:00")

    assert local_today(aware) == date(2026, 11, 13)


def test_local_day_boundaries_are_utc_three_hours_later() -> None:
    assert local_day_start_utc(date(2026, 11, 1)) == datetime(2026, 11, 1, 3, 0)
    assert local_day_end_utc(date(2026, 11, 1)) == datetime(2026, 11, 2, 3, 0)
    assert local_day_end_utc(date(2026, 12, 31)) == datetime(2027, 1, 1, 3, 0)
