"""Testes do provedor oficial da Shopee sem tocar na rede real."""

import hashlib
from collections.abc import Callable
from typing import Any

import httpx
import pytest

from app.core.errors import (
    ProviderAuthError,
    ProviderInvalidResponse,
    ProviderRateLimited,
    ProviderUnavailable,
    ValidationError,
)
from app.providers.base import ProductQuery
from app.providers.shopee import ShopeeClient, ShopeeProvider

APP_ID = "app-id-teste"
SECRET = "segredo-super-secreto"


def make_client(handler: Callable[[httpx.Request], httpx.Response], **kwargs: Any) -> ShopeeClient:
    return ShopeeClient(
        app_id=APP_ID,
        secret=SECRET,
        api_base="https://shopee.test/graphql",
        timeout=5.0,
        transport=httpx.MockTransport(handler),
        retry_base_delay=0,
        sleep=lambda _: None,
        **kwargs,
    )


def product_node(**overrides: Any) -> dict[str, Any]:
    node = {
        "itemId": 14888686365,
        "productName": "Organizador de fones",
        "productLink": "https://shopee.com.br/product/573579437/14888686365",
        "imageUrl": "https://down-br.img.susercontent.com/file/abc",
        "price": "15.49",
        "priceMin": "15.49",
        "priceMax": "19.90",
        "commissionRate": "0.53",
        "sales": 1,
        "ratingStar": 5,
        "shopId": 573579437,
        "productCatIds": [123],
    }
    node.update(overrides)
    return node


def search_response(nodes: list[dict[str, Any]], has_next: bool = False) -> dict[str, Any]:
    return {
        "data": {
            "productOfferV2": {
                "nodes": nodes,
                "pageInfo": {"page": 1, "limit": 20, "hasNextPage": has_next},
            }
        }
    }


def test_signature_covers_the_exact_utf8_body() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["authorization"] = request.headers["authorization"]
        captured["body"] = request.content
        return httpx.Response(200, json=search_response([]))

    client = make_client(handler)
    client.execute("query { produto(keyword: \"fone ção\") { itemId } }")

    parts = dict(
        part.strip().split("=", 1)
        for part in captured["authorization"].removeprefix("SHA256 ").split(",")
    )
    expected = hashlib.sha256(
        APP_ID.encode()
        + parts["Timestamp"].encode()
        + captured["body"]
        + SECRET.encode()
    ).hexdigest()

    assert parts["Credential"] == APP_ID
    assert parts["Signature"] == expected
    # O corpo precisa manter acentos: a assinatura cobre os bytes enviados.
    assert "ção".encode("utf-8") in captured["body"]
    assert b"\\u00e7" not in captured["body"]


def test_search_maps_real_fields_to_local_units() -> None:
    client = make_client(lambda request: httpx.Response(200, json=search_response([product_node()])))
    provider = ShopeeProvider(client)

    page = provider.search_products(ProductQuery(keyword="fone", page_size=20))

    assert page.total is None
    assert page.has_next is False
    assert len(page.items) == 1
    item = page.items[0]
    assert item.item_id == 14888686365
    assert item.shop_id == 573579437
    assert item.price_cents == 1549
    assert item.commission_rate_bp == 5300
    assert item.rating_x100 == 500
    assert item.sales == 1
    assert item.category is None
    assert item.source == "shopee"


def test_search_uses_explicit_list_type_and_documented_sort_types() -> None:
    payloads: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        import json

        payloads.append(json.loads(request.content))
        return httpx.Response(200, json=search_response([]))

    provider = ShopeeProvider(make_client(handler))
    provider.search_products(ProductQuery(keyword="fone", sort="commission_desc"))

    first = payloads[0]
    assert "listType: 1" in first["query"]
    assert first["variables"]["sortType"] == 5
    assert first["variables"]["limit"] == 20


def test_search_reports_has_next_from_page_info() -> None:
    client = make_client(
        lambda request: httpx.Response(
            200, json=search_response([product_node()], has_next=True)
        )
    )

    page = ShopeeProvider(client).search_products(ProductQuery())

    assert page.has_next is True


def test_search_retries_transient_system_error() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls < 3:
            return httpx.Response(
                200,
                json={
                    "errors": [
                        {
                            "message": "error [10000]: System Error",
                            "extensions": {"code": 10000},
                        }
                    ]
                },
            )
        return httpx.Response(200, json=search_response([product_node()]))

    page = ShopeeProvider(make_client(handler)).search_products(ProductQuery())

    assert calls == 3
    assert len(page.items) == 1


def test_search_gives_transient_system_error_eight_attempts() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls < 8:
            return httpx.Response(
                200, json={"errors": [{"extensions": {"code": 10000}}]}
            )
        return httpx.Response(200, json=search_response([product_node()]))

    page = ShopeeProvider(make_client(handler)).search_products(ProductQuery())

    assert calls == 8
    assert len(page.items) == 1


def test_transient_system_error_surfaces_after_eight_attempts() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200, json={"errors": [{"extensions": {"code": 10000}}]}
        )

    provider = ShopeeProvider(make_client(handler))

    with pytest.raises(ProviderUnavailable):
        provider.search_products(ProductQuery())

    assert calls == 8


def test_rate_limit_is_retried_then_surfaced() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200,
            json={
                "errors": [
                    {"extensions": {"code": 10030, "message": "Too Many Requests"}}
                ]
            },
        )

    provider = ShopeeProvider(make_client(handler))

    with pytest.raises(ProviderRateLimited):
        provider.search_products(ProductQuery())

    # Rate limit tem teto próprio de tentativas, menor que o dos erros 10000.
    assert calls == 3


@pytest.mark.parametrize("code", [10020, 10035])
def test_credential_and_access_errors_are_not_retried(code: int) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200, json={"errors": [{"extensions": {"code": code}}]}
        )

    provider = ShopeeProvider(make_client(handler))

    with pytest.raises(ProviderAuthError) as error:
        provider.search_products(ProductQuery())

    assert calls == 1
    assert SECRET not in error.value.message


def test_http_429_is_retried_as_rate_limit() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(429, headers={"Retry-After": "0"})

    provider = ShopeeProvider(make_client(handler))

    with pytest.raises(ProviderRateLimited):
        provider.search_products(ProductQuery())

    assert calls == 3


def test_invalid_parameters_are_reported_without_retry() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200, json={"errors": [{"extensions": {"code": 11001}}]}
        )

    provider = ShopeeProvider(make_client(handler))

    with pytest.raises(ProviderInvalidResponse):
        provider.search_products(ProductQuery())

    assert calls == 1


def test_mutation_is_never_retried_automatically() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200,
            json={"errors": [{"extensions": {"code": 10000}}]},
        )

    provider = ShopeeProvider(make_client(handler))

    with pytest.raises(ProviderUnavailable) as error:
        provider.create_link("https://shopee.com.br/product/1/2", ("campanha",))

    assert calls == 1
    assert "confirmar" in error.value.message
    assert SECRET not in error.value.message


def test_mutation_timeout_is_ambiguous_and_not_repeated() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ReadTimeout("timeout", request=request)

    provider = ShopeeProvider(make_client(handler))

    with pytest.raises(ProviderUnavailable) as error:
        provider.create_link("https://shopee.com.br/product/1/2", ())

    assert calls == 1
    assert "confirmar" in error.value.message


def test_create_link_sends_short_link_input_and_returns_affiliate_url() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        import json

        captured.update(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "data": {
                    "generateShortLink": {
                        "shortLink": "https://s.shopee.com.br/abc123"
                    }
                }
            },
        )

    provider = ShopeeProvider(make_client(handler))
    link = provider.create_link(
        "https://shopee.com.br/product/1/2", ("campanha", "banner")
    )

    assert captured["query"].strip().startswith("mutation")
    assert "ShortLinkInput" in captured["query"]
    assert captured["variables"] == {
        "input": {
            "originUrl": "https://shopee.com.br/product/1/2",
            "subIds": ["campanha", "banner"],
        }
    }
    assert link.affiliate_url == "https://s.shopee.com.br/abc123"
    assert link.source == "shopee"


def test_more_than_five_sub_ids_is_rejected_before_calling_the_api() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("não deveria chamar a Shopee")

    provider = ShopeeProvider(make_client(handler))

    with pytest.raises(ValidationError):
        provider.create_link("https://shopee.com.br/product/1/2", ("1", "2", "3", "4", "5", "6"))


@pytest.mark.parametrize(
    "query",
    [
        ProductQuery(category="Beleza"),
        ProductQuery(price_min_cents=1000),
        ProductQuery(min_commission_rate_bp=500),
        ProductQuery(sort="rating_desc"),
    ],
)
def test_filters_outside_provider_capabilities_are_rejected(query: ProductQuery) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("não deveria chamar a Shopee")

    provider = ShopeeProvider(make_client(handler))

    with pytest.raises(ValidationError):
        provider.search_products(query)


def test_invalid_product_node_is_reported_as_provider_error() -> None:
    node = product_node()
    node.pop("itemId")
    client = make_client(lambda request: httpx.Response(200, json=search_response([node])))

    with pytest.raises(ProviderInvalidResponse):
        ShopeeProvider(client).search_products(ProductQuery())


def test_categories_are_empty_because_the_api_has_no_catalog_of_names() -> None:
    provider = ShopeeProvider(make_client(lambda request: httpx.Response(200, json={})))

    assert provider.list_categories() == []
