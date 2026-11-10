"""Acesso a dados dos valores de Sub ID."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.time import utcnow
from app.models.sub_id import SubIdValue
from app.services.normalization import normalize_sub_id


def record_usage(session: Session, dimension: str, raw_value: str) -> SubIdValue:
    """Registra o uso de um Sub ID já normalizado.

    A forma exibida é a última digitada, mas a identidade é sempre o valor
    normalizado — por isso "Instagram" e "instagram" são o mesmo registro.
    """
    normalized = normalize_sub_id(raw_value, dimension=dimension)
    value = session.scalar(
        select(SubIdValue).where(
            SubIdValue.dimension == dimension,
            SubIdValue.normalized_value == normalized,
        )
    )

    if value is None:
        value = SubIdValue(
            dimension=dimension,
            normalized_value=normalized,
            display_value=raw_value.strip()[:64],
            usage_count=1,
            last_used_at=utcnow(),
        )
        session.add(value)
    else:
        value.usage_count += 1
        value.display_value = raw_value.strip()[:64]
        value.last_used_at = utcnow()

    session.flush()
    return value


def suggest(
    session: Session, dimension: str, term: str | None, limit: int
) -> list[SubIdValue]:
    stmt = select(SubIdValue).where(SubIdValue.dimension == dimension)
    if term:
        stmt = stmt.where(SubIdValue.normalized_value.contains(term.strip().lower()))
    stmt = stmt.order_by(
        SubIdValue.usage_count.desc(),
        SubIdValue.last_used_at.desc(),
        SubIdValue.normalized_value,
    ).limit(limit)
    return list(session.scalars(stmt).all())


def top_used(session: Session, dimension: str, limit: int = 5) -> list[SubIdValue]:
    return suggest(session, dimension, None, limit)


def count_all(session: Session, dimension: str) -> int:
    return (
        session.scalar(
            select(func.count(SubIdValue.id)).where(SubIdValue.dimension == dimension)
        )
        or 0
    )
