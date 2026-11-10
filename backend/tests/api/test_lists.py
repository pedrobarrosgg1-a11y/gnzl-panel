"""Testes dos endpoints de listas."""

from fastapi.testclient import TestClient


def _search_ids(client: TestClient, quantity: int) -> list[int]:
    items = client.get(
        "/api/products/search", params={"page_size": quantity}
    ).json()["items"]
    return [item["id"] for item in items]


def _create_list(client: TestClient, name: str = "Black Friday") -> dict:
    response = client.post("/api/lists", json={"name": name})
    assert response.status_code == 201
    return response.json()


def test_create_list_returns_created_list(client: TestClient) -> None:
    body = _create_list(client, "  Black Friday  ")

    assert body["name"] == "Black Friday"
    assert body["item_count"] == 0
    assert body["description"] is None
    assert body["created_at"].endswith("Z")


def test_duplicate_list_name_is_rejected_regardless_of_writing(
    client: TestClient,
) -> None:
    _create_list(client, "Black Friday")

    response = client.post("/api/lists", json={"name": "black_friday"})

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"
    assert "Já existe" in response.json()["error"]["message"]


def test_empty_list_name_is_rejected(client: TestClient) -> None:
    response = client.post("/api/lists", json={"name": "   "})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_list_shows_item_count(client: TestClient) -> None:
    created = _create_list(client, "Stories")
    product_ids = _search_ids(client, 2)
    client.post(f"/api/lists/{created['id']}/items", json={"product_ids": product_ids})

    body = client.get("/api/lists").json()

    assert len(body) == 1
    assert body[0]["item_count"] == 2


def test_add_products_reports_added_and_skipped(client: TestClient) -> None:
    created = _create_list(client)
    product_ids = _search_ids(client, 3)

    first = client.post(
        f"/api/lists/{created['id']}/items", json={"product_ids": product_ids}
    )
    second = client.post(
        f"/api/lists/{created['id']}/items", json={"product_ids": product_ids}
    )

    assert first.status_code == 200
    assert first.json()["added"] == 3
    assert first.json()["skipped"] == 0
    assert first.json()["item_count"] == 3
    assert second.json()["added"] == 0
    assert second.json()["skipped"] == 3


def test_add_products_keeps_order_and_product_data(client: TestClient) -> None:
    created = _create_list(client)
    product_ids = _search_ids(client, 3)

    body = client.post(
        f"/api/lists/{created['id']}/items", json={"product_ids": product_ids}
    ).json()

    assert [item["id"] for item in body["items"]] == product_ids
    assert all(item["price_cents"] > 0 for item in body["items"])


def test_add_unknown_product_is_rejected_with_details(client: TestClient) -> None:
    created = _create_list(client)
    product_ids = _search_ids(client, 1)

    response = client.post(
        f"/api/lists/{created['id']}/items",
        json={"product_ids": [*product_ids, 999_999]},
    )

    assert response.status_code == 422
    details = response.json()["error"]["details"]
    assert details["missing_product_ids"] == [999_999]


def test_add_products_to_unknown_list_returns_not_found(client: TestClient) -> None:
    response = client.post("/api/lists/424242/items", json={"product_ids": [1]})

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_list_detail_returns_products(client: TestClient) -> None:
    created = _create_list(client)
    product_ids = _search_ids(client, 2)
    client.post(f"/api/lists/{created['id']}/items", json={"product_ids": product_ids})

    body = client.get(f"/api/lists/{created['id']}").json()

    assert body["item_count"] == 2
    assert [item["id"] for item in body["items"]] == product_ids


def test_update_list_name_checks_conflict(client: TestClient) -> None:
    first = _create_list(client, "Campanha A")
    _create_list(client, "Campanha B")

    response = client.patch(
        f"/api/lists/{first['id']}", json={"name": "campanha b"}
    )

    assert response.status_code == 409


def test_update_list_description_can_be_cleared(client: TestClient) -> None:
    created = client.post(
        "/api/lists", json={"name": "Verão", "description": "Promoções de janeiro"}
    ).json()

    response = client.patch(
        f"/api/lists/{created['id']}", json={"description": None}
    )

    assert response.status_code == 200
    assert response.json()["description"] is None


def test_remove_item_from_list(client: TestClient) -> None:
    created = _create_list(client)
    product_id = _search_ids(client, 1)[0]
    client.post(
        f"/api/lists/{created['id']}/items", json={"product_ids": [product_id]}
    )

    response = client.delete(f"/api/lists/{created['id']}/items/{product_id}")

    assert response.status_code == 204
    assert client.get(f"/api/lists/{created['id']}").json()["item_count"] == 0


def test_remove_absent_item_returns_not_found(client: TestClient) -> None:
    created = _create_list(client)

    response = client.delete(f"/api/lists/{created['id']}/items/1")

    assert response.status_code == 404


def test_delete_list(client: TestClient) -> None:
    created = _create_list(client)

    response = client.delete(f"/api/lists/{created['id']}")

    assert response.status_code == 204
    assert client.get(f"/api/lists/{created['id']}").status_code == 404
    assert client.get("/api/lists").json() == []


def test_get_unknown_list_returns_not_found(client: TestClient) -> None:
    response = client.get("/api/lists/12345")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
