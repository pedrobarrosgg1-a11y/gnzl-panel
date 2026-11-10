"""Testes dos lotes de geração de links."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Product


def _search_items(
    client: TestClient, quantity: int = 3, **params
) -> list[dict]:
    response = client.get(
        "/api/products/search",
        params={"page_size": quantity, **params},
    )
    assert response.status_code == 200
    return response.json()["items"]


def _create_batch(
    client: TestClient,
    *,
    product_ids: list[int] | None = None,
    destination_type: str = "product",
    product_list_id: int | None = None,
    name: str | None = "Lote de teste",
    sub_ids: dict[str, str] | None = None,
) -> dict:
    payload: dict = {
        "name": name,
        "destination_type": destination_type,
        "product_ids": product_ids or [],
        "product_list_id": product_list_id,
    }
    if sub_ids:
        payload.update(sub_ids)
    response = client.post("/api/link-batches", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_product_batch_keeps_items_pending(client: TestClient) -> None:
    products = _search_items(client, 2)

    batch = _create_batch(
        client,
        product_ids=[product["id"] for product in products],
        sub_ids={"sub_id_1": "Instagram", "sub_id_2": "Stories"},
    )

    assert batch["status"] == "pending"
    assert batch["total_items"] == 2
    assert batch["successful_items"] == 0
    assert batch["failed_items"] == 0
    assert batch["sub_id_1"] == "instagram"
    assert batch["sub_id_2"] == "stories"
    assert batch["sub_id_3"] is None
    assert batch["source"] == "demo"
    assert batch["is_demo"] is True
    assert [item["status"] for item in batch["items"]] == ["pending", "pending"]
    assert all(item["affiliate_url"] is None for item in batch["items"])
    assert [item["product"]["id"] for item in batch["items"]] == [
        product["id"] for product in products
    ]


def test_run_batch_generates_links_for_every_item(client: TestClient) -> None:
    products = _search_items(client, 3)
    batch = _create_batch(
        client, product_ids=[product["id"] for product in products]
    )

    response = client.post(f"/api/link-batches/{batch['id']}/run")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["successful_items"] == 3
    assert body["failed_items"] == 0
    assert body["finished_at"].endswith("Z")
    assert [item["status"] for item in body["items"]] == ["success"] * 3
    assert all(item["attempts"] == 1 for item in body["items"])
    assert all(
        item["affiliate_url"].startswith("https://demo.gnzl.local/r/")
        for item in body["items"]
    )

    history = client.get("/api/links").json()
    assert history["total"] == 3
    assert {item["link_batch_id"] for item in history["items"]} == {batch["id"]}


def test_run_batch_records_partial_failure(client: TestClient) -> None:
    good = _search_items(client, 1)[0]
    failing = _search_items(client, 1, q="falha")[0]
    assert failing["item_id"] == 999_999_999

    batch = _create_batch(client, product_ids=[good["id"], failing["id"]])
    body = client.post(f"/api/link-batches/{batch['id']}/run").json()

    assert body["status"] == "partial"
    assert body["successful_items"] == 1
    assert body["failed_items"] == 1

    by_product = {item["product_id"]: item for item in body["items"]}
    assert by_product[good["id"]]["status"] == "success"
    failed = by_product[failing["id"]]
    assert failed["status"] == "failed"
    assert failed["error_code"] == "provider_unavailable"
    assert failed["error_message"]
    assert failed["affiliate_url"] is None


def test_retry_only_reprocesses_failed_items(client: TestClient) -> None:
    good = _search_items(client, 1)[0]
    failing = _search_items(client, 1, q="falha")[0]
    batch = _create_batch(client, product_ids=[good["id"], failing["id"]])
    client.post(f"/api/link-batches/{batch['id']}/run")

    body = client.post(f"/api/link-batches/{batch['id']}/run").json()

    by_product = {item["product_id"]: item for item in body["items"]}
    assert by_product[good["id"]]["attempts"] == 1
    assert by_product[failing["id"]]["attempts"] == 2
    assert body["successful_items"] == 1
    assert body["failed_items"] == 1


def test_completed_batch_cannot_run_again(client: TestClient) -> None:
    product = _search_items(client, 1)[0]
    batch = _create_batch(client, product_ids=[product["id"]])
    client.post(f"/api/link-batches/{batch['id']}/run")

    response = client.post(f"/api/link-batches/{batch['id']}/run")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


def test_list_batch_snapshots_products_when_created(client: TestClient) -> None:
    products = _search_items(client, 2)
    created = client.post(
        "/api/lists", json={"name": "Lista do lote"}
    ).json()
    client.post(
        f"/api/lists/{created['id']}/items",
        json={"product_ids": [product["id"] for product in products]},
    )

    batch = _create_batch(
        client,
        destination_type="list",
        product_list_id=created["id"],
        product_ids=[],
    )

    assert batch["destination_type"] == "list"
    assert batch["product_list_id"] == created["id"]
    assert batch["total_items"] == 2

    # A lista pode mudar depois; o lote continua com o retrato do momento.
    client.delete(
        f"/api/lists/{created['id']}/items/{products[0]['id']}"
    )
    assert client.get(f"/api/link-batches/{batch['id']}").json()["total_items"] == 2


def test_empty_list_cannot_generate_batch(client: TestClient) -> None:
    created = client.post("/api/lists", json={"name": "Vazia"}).json()

    response = client.post(
        "/api/link-batches",
        json={
            "destination_type": "list",
            "product_list_id": created["id"],
            "product_ids": [],
        },
    )

    assert response.status_code == 422
    assert "não possui produtos" in response.json()["error"]["message"]


def test_product_batch_requires_at_least_one_product(client: TestClient) -> None:
    response = client.post(
        "/api/link-batches",
        json={"destination_type": "product", "product_ids": []},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_unknown_product_is_reported(client: TestClient) -> None:
    response = client.post(
        "/api/link-batches",
        json={"destination_type": "product", "product_ids": [987_654]},
    )

    assert response.status_code == 422
    details = response.json()["error"]["details"]
    assert details["missing_product_ids"] == [987_654]


def test_product_batch_cannot_reference_a_list(client: TestClient) -> None:
    product = _search_items(client, 1)[0]

    response = client.post(
        "/api/link-batches",
        json={
            "destination_type": "product",
            "product_ids": [product["id"]],
            "product_list_id": 1,
        },
    )

    assert response.status_code == 422


def test_unknown_batch_returns_not_found(client: TestClient) -> None:
    assert client.get("/api/link-batches/9999").status_code == 404
    assert client.post("/api/link-batches/9999/run").status_code == 404


def test_batch_list_filters_and_paginates(client: TestClient) -> None:
    products = _search_items(client, 2)
    _create_batch(client, product_ids=[products[0]["id"]], name="Primeiro")
    second = _create_batch(
        client, product_ids=[products[1]["id"]], name="Segundo"
    )
    client.post(f"/api/link-batches/{second['id']}/run")

    pending = client.get(
        "/api/link-batches", params={"status": "pending", "source": "demo"}
    ).json()
    completed = client.get(
        "/api/link-batches", params={"status": "completed"}
    ).json()
    page = client.get(
        "/api/link-batches", params={"page": 1, "page_size": 1}
    ).json()

    assert [item["name"] for item in pending["items"]] == ["Primeiro"]
    assert [item["name"] for item in completed["items"]] == ["Segundo"]
    assert page["total"] == 2
    assert len(page["items"]) == 1
    assert page["has_next"] is True


def _product(session: Session, *, item_id: int, url: str, source: str) -> Product:
    product = Product(
        item_id=item_id,
        shop_id=3,
        title=f"Produto {item_id}",
        product_url=url,
        price_cents=1000,
        commission_rate_bp=500,
        data_source=source,
    )
    session.add(product)
    session.commit()
    return product


def test_batch_rejects_product_from_another_source(
    client: TestClient, session: Session
) -> None:
    product = _product(
        session,
        item_id=500,
        url="https://shopee.com.br/real-i.3.500",
        source="shopee",
    )

    response = client.post(
        "/api/link-batches",
        json={"destination_type": "product", "product_ids": [product.id]},
    )

    assert response.status_code == 422
    details = response.json()["error"]["details"]
    assert details["foreign_product_ids"] == [product.id]
    assert details["source"] == "demo"


def test_batch_dedupes_products_with_the_same_url(
    client: TestClient, session: Session
) -> None:
    url = "https://shopee.com.br/repetido-i.3.600"
    first = _product(session, item_id=600, url=url, source="demo")
    second = _product(session, item_id=601, url=url, source="demo")

    batch = _create_batch(client, product_ids=[first.id, second.id])

    assert batch["total_items"] == 1
    assert batch["items"][0]["product_id"] == first.id
