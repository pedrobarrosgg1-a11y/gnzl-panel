"""Testes de Sub IDs."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import SubIdValue
from app.services.sub_ids import SubIdService


def test_usage_is_recorded_in_normalized_form(session: Session) -> None:
    service = SubIdService(session)
    service.register_usage({"sub_id_1": "  Instagram  "})
    session.commit()

    value = session.query(SubIdValue).one()
    assert value.dimension == "sub_id_1"
    assert value.normalized_value == "instagram"
    assert value.display_value == "Instagram"
    assert value.usage_count == 1


def test_different_writings_reuse_the_same_row(session: Session) -> None:
    service = SubIdService(session)
    service.register_usage({"sub_id_1": "Black Friday"})
    service.register_usage({"sub_id_1": "black_friday"})
    session.commit()

    value = session.query(SubIdValue).one()
    assert value.normalized_value == "black-friday"
    assert value.usage_count == 2


def test_same_value_in_different_dimensions_is_separate(session: Session) -> None:
    service = SubIdService(session)
    service.register_usage({"sub_id_1": "instagram", "sub_id_2": "instagram"})
    session.commit()

    assert session.query(SubIdValue).count() == 2


def test_empty_values_are_ignored(session: Session) -> None:
    service = SubIdService(session)
    service.register_usage({"sub_id_1": "", "sub_id_2": "   "})
    session.commit()

    assert session.query(SubIdValue).count() == 0


def test_suggestions_are_ordered_by_usage(session: Session) -> None:
    service = SubIdService(session)
    for _ in range(3):
        service.register_usage({"sub_id_1": "instagram"})
    service.register_usage({"sub_id_1": "tiktok"})
    session.commit()

    suggestions = service.suggestions("sub_id_1", None)

    assert [item.normalized_value for item in suggestions] == ["instagram", "tiktok"]


def test_suggestions_filter_by_term(session: Session) -> None:
    service = SubIdService(session)
    service.register_usage({"sub_id_1": "instagram"})
    service.register_usage({"sub_id_1": "stories"})
    session.commit()

    suggestions = service.suggestions("sub_id_1", "stor")

    assert [item.normalized_value for item in suggestions] == ["stories"]


def test_suggestion_endpoint_returns_used_values(
    client: TestClient, session: Session
) -> None:
    service = SubIdService(session)
    service.register_usage({"sub_id_1": "Instagram", "sub_id_2": "stories"})
    session.commit()

    response = client.get("/api/sub-ids", params={"dimension": "sub_id_1"})

    assert response.status_code == 200
    body = response.json()
    assert body["items"][0]["value"] == "instagram"
    assert body["items"][0]["display"] == "Instagram"


def test_unknown_dimension_is_rejected(client: TestClient) -> None:
    response = client.get("/api/sub-ids", params={"dimension": "sub_id_9"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_normalize_endpoint_exposes_canonical_form(client: TestClient) -> None:
    response = client.get(
        "/api/sub-ids/normalize",
        params={"dimension": "sub_id_3", "value": "  Black FRIDAY!! "},
    )

    assert response.status_code == 200
    assert response.json() == {"normalized": "black-friday", "dimension": "sub_id_3"}


def test_normalize_endpoint_rejects_values_without_letters(client: TestClient) -> None:
    response = client.get(
        "/api/sub-ids/normalize",
        params={"dimension": "sub_id_1", "value": "@@@"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


@pytest.mark.parametrize("dimension", ["sub_id_1", "sub_id_5"])
def test_every_dimension_is_accepted(client: TestClient, dimension: str) -> None:
    response = client.get("/api/sub-ids", params={"dimension": dimension})

    assert response.status_code == 200
