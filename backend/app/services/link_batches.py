"""Serviço de lotes de geração de links.

A chamada externa acontece em threads separadas porque é I/O. A gravação no
banco, porém, fica sempre na thread da requisição: uma ``Session`` do
SQLAlchemy não é segura para uso concorrente.
"""

from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.constants import MAX_BATCH_ITEMS
from app.core.errors import AppError, ConflictError, NotFoundError, ValidationError
from app.core.time import utcnow
from app.models.link import AffiliateLink, LinkBatch, LinkBatchItem
from app.models.product import Product
from app.providers.base import GeneratedLink, LinkProvider
from app.repositories import link_batches as batches_repo
from app.repositories import links as links_repo
from app.repositories import lists as lists_repo
from app.repositories import products as products_repo
from app.services.normalization import normalize_sub_id_slots
from app.services.sub_ids import SubIdService

_SUB_ID_DIMENSIONS = ("sub_id_1", "sub_id_2", "sub_id_3", "sub_id_4", "sub_id_5")


@dataclass(frozen=True)
class _GenerationResult:
    """Resultado imutável de uma chamada ao provedor, seguro entre threads."""

    item_id: int
    link: GeneratedLink | None = None
    error_code: str | None = None
    error_message: str | None = None


def _batch_sub_ids(batch: LinkBatch) -> tuple[str | None, ...]:
    return (
        batch.sub_id_1,
        batch.sub_id_2,
        batch.sub_id_3,
        batch.sub_id_4,
        batch.sub_id_5,
    )


class LinkBatchService:
    def __init__(
        self,
        session: Session,
        link_provider: LinkProvider,
        *,
        source: str,
        concurrency: int,
    ) -> None:
        self._session = session
        self._provider = link_provider
        self._source = source
        self._concurrency = max(1, concurrency)

    # ------------------------------------------------------------------ create

    def create(
        self,
        *,
        name: str | None,
        destination_type: str,
        product_ids: Sequence[int],
        product_list_id: int | None,
        observation: str | None,
        sub_ids: Sequence[str | None],
    ) -> LinkBatch:
        products = self._resolve_products(
            destination_type=destination_type,
            product_ids=product_ids,
            product_list_id=product_list_id,
        )
        items = self._build_items(products)
        normalized_sub_ids = normalize_sub_id_slots(sub_ids)

        batch = batches_repo.create(
            self._session,
            name=name.strip() if name and name.strip() else None,
            destination_type=destination_type,
            product_list_id=product_list_id,
            observation=observation,
            sub_ids=normalized_sub_ids,
            data_source=self._source,
            total_items=len(items),
        )
        for product, original_url in items:
            batches_repo.add_item(
                self._session,
                batch,
                product=product,
                original_url=original_url,
            )

        self._session.commit()
        return batch

    def _resolve_products(
        self,
        *,
        destination_type: str,
        product_ids: Sequence[int],
        product_list_id: int | None,
    ) -> list[Product]:
        if destination_type == "product":
            if product_list_id is not None:
                raise ValidationError(
                    "Um lote de produtos não pode apontar para uma lista."
                )
            if not product_ids:
                raise ValidationError("Selecione ao menos um produto.")
            products = self._products_by_requested_order(product_ids)

        elif destination_type == "list":
            if product_ids:
                raise ValidationError(
                    "Um lote de lista não deve receber produtos avulsos."
                )
            if product_list_id is None:
                raise ValidationError("Informe a lista de origem do lote.")
            if lists_repo.get_by_id(self._session, product_list_id) is None:
                raise NotFoundError("Lista não encontrada.")
            products = lists_repo.products_of(self._session, product_list_id)
            if not products:
                raise ValidationError("A lista selecionada não possui produtos.")

        else:
            raise ValidationError(
                "Destino inválido.",
                details={"allowed": ["product", "list"]},
            )

        self._ensure_same_source(products)
        return products

    def _ensure_same_source(self, products: Sequence[Product]) -> None:
        foreign = [
            product.id for product in products if product.data_source != self._source
        ]
        if foreign:
            raise ValidationError(
                "O lote mistura produtos de outra origem de dados.",
                details={"foreign_product_ids": foreign, "source": self._source},
            )

    def _products_by_requested_order(
        self, product_ids: Sequence[int]
    ) -> list[Product]:
        unique_ids = list(dict.fromkeys(product_ids))
        found = products_repo.get_by_ids(self._session, unique_ids)
        by_id = {product.id: product for product in found}
        missing = [product_id for product_id in unique_ids if product_id not in by_id]
        if missing:
            raise ValidationError(
                "Alguns produtos não existem no catálogo local.",
                details={"missing_product_ids": missing},
            )
        return [by_id[product_id] for product_id in unique_ids]

    def _build_items(self, products: Sequence[Product]) -> list[tuple[Product, str]]:
        """Deduplica por URL: a mesma URL não pode entrar duas vezes no lote."""
        items: list[tuple[Product, str]] = []
        seen_urls: set[str] = set()
        missing_urls: list[int] = []

        for product in products:
            original_url = (product.product_url or "").strip()
            if not original_url:
                missing_urls.append(product.id)
                continue
            if original_url in seen_urls:
                continue
            seen_urls.add(original_url)
            items.append((product, original_url))

        if missing_urls:
            raise ValidationError(
                "Alguns produtos não têm URL de origem.",
                details={"missing_product_url_ids": missing_urls},
            )
        if not items:
            raise ValidationError("Nenhum produto válido para gerar links.")
        if len(items) > MAX_BATCH_ITEMS:
            raise ValidationError(
                f"Um lote aceita no máximo {MAX_BATCH_ITEMS} itens.",
                details={"total": len(items), "max": MAX_BATCH_ITEMS},
            )
        return items

    # -------------------------------------------------------------------- read

    def list_page(
        self,
        *,
        status: str | None,
        data_source: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[LinkBatch], int]:
        return batches_repo.list_page(
            self._session,
            status=status,
            data_source=data_source,
            page=page,
            page_size=page_size,
        )

    def detail(self, batch_id: int) -> LinkBatch:
        batch = batches_repo.get_by_id(self._session, batch_id, with_items=True)
        if batch is None:
            raise NotFoundError("Lote não encontrado.")
        return batch

    # --------------------------------------------------------------------- run

    def run(self, batch_id: int) -> LinkBatch:
        batch = batches_repo.get_by_id(self._session, batch_id, with_items=True)
        if batch is None:
            raise NotFoundError("Lote não encontrado.")
        if batch.status == "running":
            raise ConflictError("Este lote já está em execução.")

        items = batches_repo.items_to_process(self._session, batch_id)
        if not items:
            raise ConflictError(
                "Não há itens pendentes ou com falha para gerar neste lote."
            )

        first_run = batch.status == "pending"
        batch.status = "running"
        batch.finished_at = None
        self._session.commit()

        sub_ids = tuple(value for value in _batch_sub_ids(batch) if value)
        results = self._generate(items, sub_ids)

        try:
            self._apply_results(batch, items, results)
            self._refresh_counters(batch, first_run=first_run)
            self._session.commit()
        except Exception:
            # Nunca deixar o lote preso em "running": se a gravação falhar,
            # o estado visível passa a "failed" e o erro continua subindo.
            self._session.rollback()
            self._mark_as_failed(batch_id)
            raise

        return self.detail(batch_id)

    def _generate(
        self, items: Sequence[LinkBatchItem], sub_ids: tuple[str, ...]
    ) -> dict[int, _GenerationResult]:
        results: dict[int, _GenerationResult] = {}
        workers = max(1, min(self._concurrency, len(items)))

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(
                    self._provider.create_link, item.original_url, sub_ids
                ): item.id
                for item in items
            }
            for future in as_completed(futures):
                item_id = futures[future]
                try:
                    generated = future.result()
                except AppError as error:
                    results[item_id] = _GenerationResult(
                        item_id,
                        error_code=error.code,
                        error_message=error.message,
                    )
                except Exception:  # noqa: BLE001 - falha isolada por item
                    results[item_id] = _GenerationResult(
                        item_id,
                        error_code="provider_error",
                        error_message="Falha inesperada ao gerar o link.",
                    )
                else:
                    results[item_id] = _GenerationResult(item_id, link=generated)

        return results

    def _apply_results(
        self,
        batch: LinkBatch,
        items: Sequence[LinkBatchItem],
        results: dict[int, _GenerationResult],
    ) -> None:
        for item in items:
            result = results.get(item.id)
            if result is None:
                continue

            item.attempts += 1
            item.processed_at = utcnow()

            if result.link is None:
                item.status = "failed"
                item.error_code = result.error_code
                item.error_message = result.error_message
                continue

            if not result.link.affiliate_url.strip():
                # O CHECK do banco recusaria a linha; tratar por item mantém o
                # restante do lote íntegro em vez de derrubar a execução.
                item.status = "failed"
                item.error_code = "provider_invalid_response"
                item.error_message = "O provedor retornou um link vazio."
                continue

            # Link determinístico: se a URL já existe, o histórico é reaproveitado
            # em vez de violar a unicidade e duplicar o registro.
            link = links_repo.get_by_affiliate_url(
                self._session, result.link.affiliate_url
            )
            if link is None:
                link = AffiliateLink(
                    product_id=item.product_id,
                    link_batch_id=batch.id,
                    original_url=item.original_url,
                    affiliate_url=result.link.affiliate_url,
                    sub_id_1=batch.sub_id_1,
                    sub_id_2=batch.sub_id_2,
                    sub_id_3=batch.sub_id_3,
                    sub_id_4=batch.sub_id_4,
                    sub_id_5=batch.sub_id_5,
                    data_source=batch.data_source,
                    status="active",
                )
                self._session.add(link)
                self._session.flush()

            item.status = "success"
            item.affiliate_link = link
            item.affiliate_link_id = link.id
            item.error_code = None
            item.error_message = None

    def _refresh_counters(self, batch: LinkBatch, *, first_run: bool) -> None:
        counts = batches_repo.counts_by_status(self._session, batch.id)
        batch.successful_items = counts.get("success", 0)
        batch.failed_items = counts.get("failed", 0)
        batch.finished_at = utcnow()

        if batch.failed_items == 0:
            batch.status = "completed"
        elif batch.successful_items == 0:
            batch.status = "failed"
        else:
            batch.status = "partial"

        # O autocomplete conta uso real, não tentativa: registra apenas na
        # primeira execução e somente se ao menos um link foi gerado.
        if first_run and batch.successful_items:
            values = {
                dimension: value
                for dimension, value in zip(_SUB_ID_DIMENSIONS, _batch_sub_ids(batch))
                if value
            }
            if values:
                SubIdService(self._session).register_usage(values)

    def _mark_as_failed(self, batch_id: int) -> None:
        batch = batches_repo.get_by_id(self._session, batch_id)
        if batch is None:
            return
        batch.status = "failed"
        batch.finished_at = utcnow()
        self._session.commit()
