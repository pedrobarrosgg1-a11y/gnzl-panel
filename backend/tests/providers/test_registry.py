"""Testes da montagem de provedores."""

import pytest

from app.core.config import Settings
from app.core.errors import ConfigurationError
from app.providers.demo import DemoProvider
from app.providers.registry import build_providers


def test_demo_is_the_default_provider() -> None:
    providers = build_providers(Settings(provider="demo"))

    assert isinstance(providers.product, DemoProvider)
    assert isinstance(providers.link, DemoProvider)
    assert providers.source == "demo"


def test_shopee_without_credentials_fails_with_actionable_message() -> None:
    settings = Settings(provider="shopee", shopee_app_id="", shopee_secret="")

    with pytest.raises(ConfigurationError) as error:
        build_providers(settings)

    assert "GNZL_SHOPEE_APP_ID" in error.value.message
    assert "GNZL_SHOPEE_SECRET" in error.value.message


def test_shopee_with_credentials_is_not_silently_replaced_by_demo() -> None:
    settings = Settings(
        provider="shopee", shopee_app_id="app", shopee_secret="secret"
    )

    with pytest.raises(ConfigurationError) as error:
        build_providers(settings)

    assert "demo" not in error.value.message.lower().replace(
        "use gnzl_provider=demo", ""
    )
