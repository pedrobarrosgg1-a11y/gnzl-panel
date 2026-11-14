"""Testes das regras compartilhadas de normalização de conversões."""

import pytest

from app.core.conversion_rules import (
    MAX_CHANNEL_LENGTH,
    MAX_SUB_IDS,
    normalize_channel,
    split_sub_ids,
    status_group_from_raw,
    truncate_text,
)


@pytest.mark.parametrize(
    ("raw", "group"),
    [
        ("COMPLETED", "approved"),
        ("completed", "approved"),
        ("Aprovado", "approved"),
        ("Concluído", "approved"),
        ("Pago", "approved"),
        ("Entregue", "approved"),
        ("CANCELLED", "cancelled"),
        ("Cancelado", "cancelled"),
        ("REFUNDED", "refunded"),
        ("Devolvido", "refunded"),
        ("Reembolsado", "refunded"),
        ("PENDING", "pending"),
        ("Aguardando pagamento", "pending"),
        ("Não pago", "pending"),
        ("PROCESSING", "pending"),
        ("ALL", "unknown"),
        ("Status novo da fonte", "unknown"),
        ("", "unknown"),
        (None, "unknown"),
    ],
)
def test_status_group_from_raw(raw: str | None, group: str) -> None:
    assert status_group_from_raw(raw) == group


def test_nao_pago_is_pending_even_though_it_contains_pago() -> None:
    assert status_group_from_raw("NÃO PAGO") == "pending"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Campanha, Banner;black-friday|extra cinco", (
            "campanha",
            "banner",
            "black-friday",
            "extra",
            "cinco",
        )),
        ("Promoção 2026", ("promocao", "2026", None, None, None)),
        ("  Ação/Verão  ", ("acaoverao", None, None, None, None)),
        ("a b c d e f", ("a", "b", "c", "d", "e")),
        ("", (None,) * MAX_SUB_IDS),
        (None, (None,) * MAX_SUB_IDS),
    ],
)
def test_split_sub_ids(
    raw: str | None, expected: tuple[str | None, ...]
) -> None:
    assert split_sub_ids(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("app", "APP"),
        ("App", "APP"),
        ("APP", "APP"),
        ("web", "WEB"),
        ("  mobile  ", "MOBILE"),
        ("Instagram", "Instagram"),
        ("   ", None),
        (None, None),
    ],
)
def test_normalize_channel(raw: str | None, expected: str | None) -> None:
    assert normalize_channel(raw) == expected


def test_normalize_channel_truncates_to_the_column_limit() -> None:
    assert normalize_channel("x" * 200) == "x" * MAX_CHANNEL_LENGTH


def test_truncate_text_strips_and_limits() -> None:
    assert truncate_text("  Fone  ", 10) == "Fone"
    assert truncate_text("abcdef", 3) == "abc"
    assert truncate_text("   ", 10) is None
    assert truncate_text(None, 10) is None
