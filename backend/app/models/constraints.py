"""Constraints reutilizadas por mais de uma entidade."""

from sqlalchemy import CheckConstraint

from app.core.constants import SUB_ID_MAX_LENGTH


def sub_id_format_constraint(column: str) -> CheckConstraint:
    """Formato canônico: minúsculas, dígitos e hífen. Sem acento, espaço ou maiúscula."""
    return CheckConstraint(
        f"{column} IS NULL OR ("
        f"{column} NOT GLOB '*[^a-z0-9-]*' "
        f"AND length({column}) BETWEEN 1 AND {SUB_ID_MAX_LENGTH})",
        name=f"{column}_format",
    )
