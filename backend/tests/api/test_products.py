"""Testes da busca de produtos pela API."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Product


def test_search_returns_demo_page(client: TestClient) -> None:
    response = client.get("/api/products/search")

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 20
    assert body["page"] == 1
    assert body["has_next"] is True
    assert body["total"] > 20
    assert body["source"] == "demo"
    assert body["is_demo"] is True


def test_search_result_carries_every_field_needed_by_the_ui(
    client: TestClient,
) -> None:
    item = client.get("/api/products/search").json()["items"][0]

    assert set(item) == {
        "id",
        "item_id",
        "shop_id",
        "title",
        "image_url",
        "product_url",
        "price_cents",
        "commission_rate_bp",
        "sales",
        "rating_x100",
        "category",
        "source",
    }
    assert item["price_cents"] > 0
    assert item["product_url"].startswith("https://shopee.com.br/")


def test_search_persists_products_for_lists_and_history(
    client: TestClient, session: Session
) -> None:
    client.get("/api/products/search", params={"page_size": 5})

    assert session.query(Product).count() == 5


def test_search_is_idempotent_for_the_same_page(
    client: TestClient, session: Session
) -> None:
    first = client.get("/api/products/search", params={"page_size": 5}).json()
    second = client.get("/api/products/search", params={"page_size": 5}).json()

    assert [item["id"] for item in first["items"]] == [
        item["id"] for item in second["items"]
    ]
    assert session.query(Product).count() == 5


def test_search_filters_by_keyword(client: TestClient) -> None:
    body = client.get("/api/products/search", params={"q": "air fryer"}).json()

    assert body["items"]
    assert all("air fryer" in item["title"].lower() for item in body["items"])


def test_search_filters_by_category(client: TestClient) -> None:
    body = client.get(
        "/api/products/search", params={"category": "Beleza", "page_size": 100}
    ).json()

    assert body["items"]
    assert {item["category"] for item in body["items"]} == {"Beleza"}


def test_search_filters_by_price_range(client: TestClient) -> None:
    body = client.get(
        "/api/products/search",
        params={"price_min_cents": 5000, "price_max_cents": 10000, "page_size": 100},
    ).json()

    assert body["items"]
    assert all(5000 <= item["price_cents"] <= 10000 for item in body["items"])


def test_search_sorts_by_commission(client: TestClient) -> None:
    body = client.get(
        "/api/products/search",
        params={"sort": "commission_desc", "page_size": 100},
    ).json()

    rates = [item["commission_rate_bp"] for item in body["items"]]
    assert rates == sorted(rates, reverse=True)


def test_search_paginates_without_repeating(client: TestClient) -> None:
    first = client.get("/api/products/search", params={"page": 1, "page_size": 5}).json()
    second = client.get("/api/products/search", params={"page": 2, "page_size": 5}).json()

    first_ids = {item["id"] for item in first["items"]}
    second_ids = {item["id"] for item in second["items"]}
    assert first_ids.isdisjoint(second_ids)


def test_invalid_price_range_returns_validation_error(client: TestClient) -> None:
    response = client.get(
        "/api/products/search",
        params={"price_min_cents": 900, "price_max_cents": 100},
    )

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert "preço mínimo" in error["message"]
    assert error["request_id"]


def test_page_size_above_limit_returns_validation_error(client: TestClient) -> None:
    response = client.get("/api/products/search", params={"page_size": 101})

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert error["details"]["fields"]


def test_unknown_sort_is_rejected(client: TestClient) -> None:
    response = client.get("/api/products/search", params={"sort": "inventado"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_categories_come_from_the_provider(client: TestClient) -> None:
    body = client.get("/api/products/categories").json()

    assert body["source"] == "demo"
    assert body["is_demo"] is True
    assert "Beleza" in body["items"]
    assert body["items"] == sorted(body["items"], key=str.casefold)
