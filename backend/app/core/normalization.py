"""Primitivas de normalização textual usadas por mais de uma camada.

Ficam em ``core`` porque não pertencem a um serviço específico: o mesmo
``normalize_key`` canônico é usado por listas, Sub IDs digitados à mão e pelos
Sub IDs que chegam de relatórios externos.
"""

import re
import unicodedata

from app.core.constants import LIST_NAME_MAX_LENGTH

_SEPARATORS = re.compile(r"[\s_]+")
_INVALID_CHARS = re.compile(r"[^a-z0-9-]+")
_REPEATED_HYPHENS = re.compile(r"-{2,}")


def normalize_key(value: str, *, max_length: int = LIST_NAME_MAX_LENGTH) -> str:
    """Minúsculas, sem acento, apenas ``a-z0-9-``, sem hífens nas pontas.

    Retorna string vazia se nada aproveitável sobrar — quem chama decide se
    isso é erro.
    """
    without_accents = (
        unicodedata.normalize("NFKD", value.strip()).encode("ascii", "ignore").decode()
    )
    with_separators = _SEPARATORS.sub("-", without_accents.lower())
    cleaned = _INVALID_CHARS.sub("", with_separators)
    collapsed = _REPEATED_HYPHENS.sub("-", cleaned).strip("-")
    return collapsed[:max_length].strip("-")
