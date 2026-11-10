"""Testes do histórico e da regeneração de links."""

from fastapi.testclient import TestClient


def _search_items(
    client: TestClient, quantity: int = 1, **params
) -> list[dict]:
    response = client.get(
        "/api/products/search",
        params={"page_size": quantity, **params},
    )
    assert response.status_code == 200
    return response.json()["items"]


def _create_and_run_batch(
    client: TestClient,
    product_ids: list[int],
    *,
    sub_ids: dict[str, str] | None = None,
) -> dict:
    payload: dict = {
        "destination_type": "product",
        "product_ids": product_ids,
    }
    if sub_ids:
        payload.update(sub_ids)
    created = client.post("/api/link-batches", json=payload)
    assert created.status_code == 201, created.text
    batch_id = created.json()["id"]

    response = client.post(f"/api/link-batches/{batch_id}/run")
    assert response.status_code == 200, response.text
    return response.json()


def test_history_lists_generated_links_with_product(client: TestClient) -> None:
    products = _search_items(client, 2)
    batch = _create_and_run_batch(
        client,
        [product["id"] for product in products],
        sub_ids={"sub_id_1": "Instagram", "sub_id_2": "Feed"},
    )

    history = client.get("/api/links").json()

    assert history["total"] == 2
    assert history["items"][0]["link_batch_id"] == batch["id"]
    assert history["items"][0]["source"] == "demo"
    assert history["items"][0]["is_demo"] is True
    assert history["items"][0]["sub_id_1"] == "instagram"
    assert history["items"][0]["sub_id_2"] == "feed"
    assert history["items"][0]["product"]["id"] in {
        product["id"] for product in products
    }


def test_history_filters_by_batch_status_and_sub_id(client: TestClient) -> None:
    product = _search_items(client, 1)[0]
    batch = _create_and_run_batch(
        client, [product["id"]], sub_ids={"sub_id_1": "Instagram"}
    )
    other = _search_items(client, 1, page=2)[0]
    _create_and_run_batch(client, [other["id"]], sub_ids={"sub_id_1": "TikTok"})

    by_sub_id = client.get(
        "/api/links", params={"sub_id_1": "instagram"}
    ).json()
    by_batch = client.get(
        "/api/links", params={"batch_id": batch["id"]}
    ).json()
    active = client.get("/api/links", params={"status": "active"}).json()
    replaced = client.get("/api/links", params={"status": "replaced"}).json()

    assert by_sub_id["total"] == 1
    assert by_sub_id["items"][0]["product_id"] == product["id"]
    assert by_batch["total"] == 1
    assert active["total"] == 2
    assert replaced["total"] == 0


def test_history_searches_by_product_title(client: TestClient) -> None:
    product = _search_items(client, 1)[0]
    _create_and_run_batch(client, [product["id"]])
    term = product["title"].split()[0]

    body = client.get("/api/links", params={"q": term}).json()

    assert body["total"] == 1
    assert term.lower() in body["items"][0]["product"]["title"].lower()


def test_link_detail_returns_the_generated_link(client: TestClient) -> None:
    product = _search_items(client, 1)[0]
    _create_and_run_batch(client, [product["id"]])

    link_id = client.get("/api/links").json()["items"][0]["id"]
    body = client.get(f"/api/links/{link_id}").json()

    assert body["id"] == link_id
    assert body["affiliate_url"].startswith("https://demo.gnzl.local/r/")
    assert body["original_url"] == product["product_url"]
    assert body["status"] == "active"


def test_regenerate_creates_new_link_and_replaces_old(client: TestClient) -> None:
    product = _search_items(client, 1)[0]
    batch = _create_and_run_batch(
        client, [product["id"]], sub_ids={"sub_id_1": "Instagram"}
    )
    old = batch["items"][0]
    old_link = client.get(f"/api/links/{old['affiliate_link_id']}").json()

    response = client.post(
        f"/api/links/{old_link['id']}/regenerate",
        json={"sub_id_1": "TikTok"},
    )

    assert response.status_code == 200
    new_link = response.json()
    assert new_link["id"] != old_link["id"]
    assert new_link["status"] == "active"
    assert new_link["sub_id_1"] == "tiktok"
    assert new_link["affiliate_url"] != old_link["affiliate_url"]
    assert new_link["link_batch_id"] == old_link["link_batch_id"]

    previous = client.get(f"/api/links/{old_link['id']}").json()
    assert previous["status"] == "replaced"
    assert previous["replaced_by_id"] == new_link["id"]


def test_regenerate_without_changing_sub_ids_is_rejected(
    client: TestClient,
) -> None:
    product = _search_items(client, 1)[0]
    batch = _create_and_run_batch(
        client, [product["id"]], sub_ids={"sub_id_1": "Instagram"}
    )
    link_id = batch["items"][0]["affiliate_link_id"]

    response = client.post(f"/api/links/{link_id}/regenerate", json={})

    assert response.status_code == 409
    assert "mesmo link" in response.json()["error"]["message"]


def test_replaced_link_cannot_be_regenerated_again(client: TestClient) -> None:
    product = _search_items(client, 1)[0]
    batch = _create_and_run_batch(
        client, [product["id"]], sub_ids={"sub_id_1": "Instagram"}
    )
    link_id = batch["items"][0]["affiliate_link_id"]
    client.post(
        f"/api/links/{link_id}/regenerate", json={"sub_id_1": "TikTok"}
    )

    response = client.post(
        f"/api/links/{link_id}/regenerate", json={"sub_id_1": "Facebook"}
    )

    assert response.status_code == 409
    assert "somente links ativos" in response.json()["error"]["message"].lower()


def test_same_url_is_reused_instead_of_duplicated(client: TestClient) -> None:
    product = _search_items(client, 1)[0]
    sub_ids = {"sub_id_1": "Instagram", "sub_id_2": "Feed"}
    first = _create_and_run_batch(client, [product["id"]], sub_ids=sub_ids)
    second = _create_and_run_batch(client, [product["id"]], sub_ids=sub_ids)

    history = client.get("/api/links").json()

    assert history["total"] == 1
    assert (
        first["items"][0]["affiliate_link_id"]
        == second["items"][0]["affiliate_link_id"]
    )
    assert second["status"] == "completed"


def test_unknown_link_returns_not_found(client: TestClient) -> None:
    assert client.get("/api/links/424242").status_code == 404
    assert (
        client.post("/api/links/424242/regenerate", json={}).status_code == 404
    )
