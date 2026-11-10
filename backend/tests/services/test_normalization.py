"""Testes da normalização de valores digitados."""

import pytest

from app.core.errors import ValidationError
from app.services.normalization import normalize_key, normalize_list_name, normalize_sub_id


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Black Friday", "black-friday"),
        ("  BLACK_FRIDAY  ", "black-friday"),
        ("black   friday", "black-friday"),
        ("black--friday", "black-friday"),
        ("Ação de Verão", "acao-de-verao"),
        ("instagram!", "instagram"),
        ("stories/feed", "storiesfeed"),
        ("-promo-", "promo"),
    ],
)
def test_normalize_key(raw: str, expected: str) -> None:
    assert normalize_key(raw) == expected


def test_normalize_key_can_return_empty() -> None:
    assert normalize_key("!!! ") == ""


def test_normalize_list_name_rejects_empty_result() -> None:
    with pytest.raises(ValidationError):
        normalize_list_name("###")


def test_normalize_sub_id_reports_dimension() -> None:
    with pytest.raises(ValidationError) as error:
        normalize_sub_id("   ", dimension="sub_id_2")

    assert error.value.details == {"dimension": "sub_id_2"}


def test_normalize_sub_id_respects_max_length() -> None:
    assert normalize_sub_id("a" * 200, dimension="sub_id_1") == "a" * 64
