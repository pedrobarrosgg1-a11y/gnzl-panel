"""Testes do provedor de demonstração."""

import pytest

from app.core.errors import ProviderUnavailable, ValidationError
from app.providers.base import LinkProvider, ProductProvider, ProductQuery
from app.providers.demo import DEMO_FAILING_ITEM_ID, DEMO_PRODUCTS, DemoProvider
from app.providers.demo.catalog import DEMO_PRODUCTS as CATALOG


@pytest.fixture
def provider() -> DemoProvider:
    return DemoProvider()


def test_implements_both_provider_contracts(provider: DemoProvider) -> None:
    assert isinstance(provider, ProductProvider)
    assert isinstance(provider, LinkProvider)


def test_default_search_returns_first_page_with_total(provider: DemoProvider) -> None:
    page = provider.search_products(ProductQuery(page_size=10))

    assert len(page.items) == 10
    assert page.total == len(CATALOG)
    assert page.has_next is True
    assert page.items[0].source == "demo"


def test_search_ignores_accents_and_case(provider: DemoProvider) -> None:
    by_accent = provider.search_products(ProductQuery(keyword="ácido"))
    by_plain = provider.search_products(ProductQuery(keyword="ACIDO"))

    assert [item.item_id for item in by_accent.items] == [
        item.item_id for item in by_plain.items
    ]
    assert len(by_accent.items) == 1


def test_search_filters_by_category(provider: DemoProvider) -> None:
    page = provider.search_products(ProductQuery(category="beleza", page_size=100))

    assert page.items
    assert all(item.category == "Beleza" for item in page.items)


def test_search_filters_by_price_range(provider: DemoProvider) -> None:
    page = provider.search_products(
        ProductQuery(price_min_cents=5000, price_max_cents=10000, page_size=100)
    )

    assert page.items
    assert all(5000 <= item.price_cents <= 10000 for item in page.items)


def test_search_filters_by_minimum_commission(provider: DemoProvider) -> None:
    page = provider.search_products(
        ProductQuery(min_commission_rate_bp=1200, page_size=100)
    )

    assert page.items
    assert all(item.commission_rate_bp >= 1200 for item in page.items)


@pytest.mark.parametrize(
    ("sort", "key"),
    [
        ("commission_desc", lambda item: -item.commission_rate_bp),
        ("price_asc", lambda item: item.price_cents),
        ("price_desc", lambda item: -item.price_cents),
        ("sales_desc", lambda item: -(item.sales or 0)),
        ("rating_desc", lambda item: -(item.rating_x100 or 0)),
    ],
)
def test_search_respects_sorting(provider: DemoProvider, sort: str, key) -> None:
    page = provider.search_products(ProductQuery(sort=sort, page_size=100))

    assert page.items
    values = [key(item) for item in page.items]
    assert values == sorted(values)


def test_pagination_does_not_repeat_items(provider: DemoProvider) -> None:
    first = provider.search_products(ProductQuery(page=1, page_size=5))
    second = provider.search_products(ProductQuery(page=2, page_size=5))

    first_ids = {item.item_id for item in first.items}
    second_ids = {item.item_id for item in second.items}

    assert len(first.items) == 5
    assert len(second.items) == 5
    assert first_ids.isdisjoint(second_ids)


def test_last_page_has_no_next(provider: DemoProvider) -> None:
    page_size = 100
    page = provider.search_products(ProductQuery(page=1, page_size=page_size))

    assert page.has_next is False


@pytest.mark.parametrize("page_size", [0, 101])
def test_invalid_page_size_is_rejected(provider: DemoProvider, page_size: int) -> None:
    with pytest.raises(ValidationError):
        provider.search_products(ProductQuery(page_size=page_size))


def test_search_is_deterministic(provider: DemoProvider) -> None:
    query = ProductQuery(keyword="pet", sort="sales_desc")

    first = provider.search_products(query)
    second = DemoProvider().search_products(query)

    assert first == second


def test_create_link_is_deterministic_for_same_input(provider: DemoProvider) -> None:
    url = DEMO_PRODUCTS[0].product_url
    subs = ("instagram", "stories", "black-friday")

    first = provider.create_link(url, subs)
    second = provider.create_link(url, subs)

    assert first == second
    assert first.affiliate_url.startswith("https://demo.gnzl.local/r/")
    assert first.source == "demo"


def test_different_sub_ids_generate_different_links(provider: DemoProvider) -> None:
    url = DEMO_PRODUCTS[0].product_url

    a = provider.create_link(url, ("instagram",))
    b = provider.create_link(url, ("tiktok",))

    assert a.affiliate_url != b.affiliate_url


def test_create_link_requires_url(provider: DemoProvider) -> None:
    with pytest.raises(ValidationError):
        provider.create_link("   ", ())


def test_create_link_rejects_more_than_five_sub_ids(provider: DemoProvider) -> None:
    with pytest.raises(ValidationError):
        provider.create_link(DEMO_PRODUCTS[0].product_url, ("a", "b", "c", "d", "e", "f"))


def test_failing_demo_product_raises_provider_unavailable(provider: DemoProvider) -> None:
    with pytest.raises(ProviderUnavailable):
        provider.create_link(
            f"https://shopee.com.br/produto-i.9000.{DEMO_FAILING_ITEM_ID}", ()
        )
