"""Serviço de Sub IDs: normalização, registro de uso e sugestões."""

from collections.abc import Mapping

from sqlalchemy.orm import Session

from app.core.errors import ValidationError
from app.models.sub_id import SUB_ID_DIMENSIONS, SubIdValue
from app.repositories import sub_ids as sub_ids_repo
from app.services.normalization import normalize_sub_id


def normalize_dimension(dimension: str) -> str:
    if dimension not in SUB_ID_DIMENSIONS:
        raise ValidationError(
            "Dimensão de Sub ID inválida.",
            details={"allowed": list(SUB_ID_DIMENSIONS)},
        )
    return dimension


class SubIdService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def suggestions(
        self, dimension: str, term: str | None, limit: int = 10
    ) -> list[SubIdValue]:
        return sub_ids_repo.suggest(
            self._session, normalize_dimension(dimension), term, limit
        )

    def normalize_preview(self, dimension: str, value: str) -> str:
        return normalize_sub_id(value, dimension=normalize_dimension(dimension))

    def register_usage(self, values: Mapping[str, str]) -> None:
        """Grava o uso de cada Sub ID informado. Ignora valores vazios.

        Não faz commit: quem chama (geração de links) controla a transação.
        """
        for dimension, raw_value in values.items():
            if raw_value is None or not raw_value.strip():
                continue
            sub_ids_repo.record_usage(
                self._session, normalize_dimension(dimension), raw_value
            )
