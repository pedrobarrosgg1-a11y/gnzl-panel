"""Normalização de valores digitados pelo usuário.

Uma única forma canônica evita duplicidade causada por diferença de escrita:
"Black Friday", "black-friday " e "BLACK_FRIDAY" viram ``black-friday``.
A primitiva textual vive em ``app.core.normalization`` para ser reaproveitada
pelos relatórios importados sem criar dependência de serviço para serviço.
"""

from collections.abc import Sequence

from app.core.constants import LIST_NAME_MAX_LENGTH, SUB_ID_MAX_LENGTH
from app.core.errors import ValidationError
from app.core.normalization import normalize_key

__all__ = [
    "normalize_key",
    "normalize_list_name",
    "normalize_sub_id",
    "normalize_sub_id_slots",
]


def normalize_list_name(value: str) -> str:
    normalized = normalize_key(value, max_length=LIST_NAME_MAX_LENGTH)
    if not normalized:
        raise ValidationError(
            "O nome da lista precisa ter ao menos uma letra ou número."
        )
    return normalized


def normalize_sub_id(value: str, *, dimension: str) -> str:
    normalized = normalize_key(value, max_length=SUB_ID_MAX_LENGTH)
    if not normalized:
        raise ValidationError(
            "O Sub ID precisa ter ao menos uma letra ou número.",
            details={"dimension": dimension},
        )
    return normalized


def normalize_sub_id_slots(
    raw_values: Sequence[str | None],
) -> tuple[str | None, ...]:
    """Normaliza as cinco posições de Sub ID.

    Posições vazias viram ``None`` para que o banco guarde ausência, não uma
    string vazia que violaria o CHECK de formato.
    """
    normalized: list[str | None] = []
    for index, raw_value in enumerate(raw_values, start=1):
        if raw_value is None or not raw_value.strip():
            normalized.append(None)
        else:
            normalized.append(normalize_sub_id(raw_value, dimension=f"sub_id_{index}"))
    return tuple(normalized)
