"""Testes do serviço de lotes com um provedor controlado."""

import hashlib
from collections import Counter

from sqlalchemy.orm import Session

from app.core.errors import ProviderUnavailable
from app.models import Product, SubIdValue
from app.providers.base import GeneratedLink
from app.services.link_batches import LinkBatchService


class FlakyProvider:
    """Falha as primeiras chamadas de URLs escolhidas e depois funciona."""

    name = "demo"
    is_demo = True

    def __init__(self, fail_urls: set[str], failures: int = 1) -> None:
        self._fail_urls = fail_urls
        self._failures = failures
        self.calls: Counter[str] = Counter()

    def create_link(self, origin_url: str, sub_ids: tuple[str, ...]) -> GeneratedLink:
        self.calls[origin_url] += 1
        if (
            origin_url in self._fail_urls
            and self.calls[origin_url] <= self._failures
        ):
            raise ProviderUnavailable("Falha temporária simulada.")

        digest = hashlib.sha256(
            f"{origin_url}|{','.join(sub_ids)}".encode()
        ).hexdigest()
        return GeneratedLink(
            original_url=origin_url,
            affiliate_url=f"https://flaky.local/r/{digest[:12]}",
            source="demo",
        )


class AlwaysFailingProvider:
    name = "demo"
    is_demo = True

    def create_link(self, origin_url: str, sub_ids: tuple[str, ...]) -> GeneratedLink:
        raise ProviderUnavailable("Provedor indisponível.")


def _add_product(session: Session, item_id: int, url: str) -> Product:
    product = Product(
        item_id=item_id,
        shop_id=7,
        title=f"Produto {item_id}",
        product_url=url,
        price_cents=1000,
        commission_rate_bp=500,
        data_source="demo",
    )
    session.add(product)
    session.commit()
    return product


def _create_batch(
    session: Session, provider, product_ids: list[int]
) -> LinkBatchService:
    service = LinkBatchService(
        session, provider, source="demo", concurrency=2
    )
    service.create(
        name="Lote controlado",
        destination_type="product",
        product_ids=product_ids,
        product_list_id=None,
        observation=None,
        sub_ids=("Instagram", "Stories", None, None, None),
    )
    return service


def test_retry_turns_partial_into_completed(session: Session) -> None:
    good = _add_product(session, 1, "https://shopee.com.br/bom-i.1.1")
    flaky = _add_product(session, 2, "https://shopee.com.br/instavel-i.1.2")
    provider = FlakyProvider({flaky.product_url})

    service = _create_batch(session, provider, [good.id, flaky.id])
    first = service.run(1)

    assert first.status == "partial"
    assert first.successful_items == 1
    assert first.failed_items == 1
    attempts = {item.product_id: item.attempts for item in first.items}
    assert attempts == {good.id: 1, flaky.id: 1}

    second = service.run(1)

    assert second.status == "completed"
    assert second.successful_items == 2
    assert second.failed_items == 0
    attempts = {item.product_id: item.attempts for item in second.items}
    assert attempts == {good.id: 1, flaky.id: 2}
    assert all(item.status == "success" for item in second.items)
    assert all(item.error_message is None for item in second.items)


def test_usage_is_registered_only_once_across_retries(session: Session) -> None:
    good = _add_product(session, 10, "https://shopee.com.br/ok-i.1.10")
    flaky = _add_product(session, 11, "https://shopee.com.br/retry-i.1.11")
    provider = FlakyProvider({flaky.product_url})
    service = _create_batch(session, provider, [good.id, flaky.id])

    service.run(1)
    service.run(1)

    values = {
        value.dimension: value
        for value in session.query(SubIdValue).all()
    }
    assert values["sub_id_1"].normalized_value == "instagram"
    assert values["sub_id_1"].usage_count == 1
    assert values["sub_id_2"].normalized_value == "stories"
    assert values["sub_id_2"].usage_count == 1


def test_batch_with_only_failures_is_marked_failed(session: Session) -> None:
    product = _add_product(session, 20, "https://shopee.com.br/falha-i.1.20")
    service = _create_batch(
        session, AlwaysFailingProvider(), [product.id]
    )

    batch = service.run(1)

    assert batch.status == "failed"
    assert batch.successful_items == 0
    assert batch.failed_items == 1
    assert session.query(SubIdValue).count() == 0
