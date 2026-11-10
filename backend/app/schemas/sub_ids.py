"""Schemas de Sub IDs."""

from typing import Literal

from pydantic import BaseModel

from app.models.sub_id import SubIdValue
from app.schemas.common import UtcDateTime

SubIdDimension = Literal["sub_id_1", "sub_id_2", "sub_id_3", "sub_id_4", "sub_id_5"]


class SubIdSuggestion(BaseModel):
    value: str
    display: str
    usage_count: int
    last_used_at: UtcDateTime | None

    @classmethod
    def from_model(cls, value: SubIdValue) -> "SubIdSuggestion":
        return cls(
            value=value.normalized_value,
            display=value.display_value,
            usage_count=value.usage_count,
            last_used_at=value.last_used_at,
        )


class SubIdListResponse(BaseModel):
    items: list[SubIdSuggestion]


class NormalizeResponse(BaseModel):
    normalized: str
    dimension: SubIdDimension
