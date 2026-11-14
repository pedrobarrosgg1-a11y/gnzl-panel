"""Provedor oficial de afiliados da Shopee (busca e geração de links)."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from app.core.constants import (
    MAX_CONVERSION_WINDOW_DAYS,
    MAX_PAGE_SIZE,
    PRODUCT_TITLE_MAX_LENGTH,
)
from app.core.conversion_rules import (
    DEFAULT_QUANTITY,
    MAX_ORDER_ID_LENGTH,
    MAX_STATUS_LENGTH,
    MAX_SUB_IDS,
    normalize_channel,
    split_sub_ids,
    status_group_from_raw,
    truncate_text,
)
from app.core.errors import (
    ProviderInvalidResponse,
    ProviderUnavailable,
    ValidationError,
)
from app.core.time import utcnow
from app.providers.base import (
    SOURCE_SHOPEE,
    ConversionQuery,
    ConversionRecord,
    GeneratedLink,
    ProductPage,
    ProductQuery,
    ProductRecord,
)
from app.providers.shopee.client import ShopeeClient

# A API limita a página a 500 e devolve um cursor com validade curta. O teto de
# páginas evita um laço infinito se a fonte repetir o mesmo cursor.
CONVERSION_PAGE_LIMIT = 500
MAX_CONVERSION_PAGES = 100

# Valores documentados em affiliate.shopee.com.br/open_api.
LIST_TYPE_MAIOR_COMISSAO = 1
SORT_TYPES = {
    "relevance": 1,
    "sales_desc": 2,
    "price_desc": 3,
    "price_asc": 4,
    "commission_desc": 5,
}

_PRODUCT_FIELDS = """
      itemId
      productName
      productLink
      imageUrl
      price
      priceMin
      priceMax
      commissionRate
      sales
      ratingStar
      shopId
      productCatIds
"""

_SEARCH_QUERY = f"""
query ($keyword: String, $page: Int, $limit: Int, $sortType: Int) {{
  productOfferV2(
    listType: {LIST_TYPE_MAIOR_COMISSAO}
    keyword: $keyword
    page: $page
    limit: $limit
    sortType: $sortType
  ) {{
    nodes {{
      {_PRODUCT_FIELDS}
    }}
    pageInfo {{
      page
      limit
      hasNextPage
    }}
  }}
}}
"""

_SHORT_LINK_MUTATION = """
mutation ($input: ShortLinkInput!) {
  generateShortLink(input: $input) {
    shortLink
  }
}
"""

# ``purchaseTimeStart``/``purchaseTimeEnd`` são Int64. A API recusa variáveis
# desse tipo com "wrong type", por isso os tempos entram inline; ``Int`` e
# ``String`` funcionam como variáveis e permanecem assim.
_CONVERSION_QUERY = """
query ($limit: Int, $scrollId: String) {{
  conversionReport(
    purchaseTimeStart: {start}
    purchaseTimeEnd: {end}
    conversionStatus: ALL
    limit: $limit
    scrollId: $scrollId
  ) {{
    nodes {{
      purchaseTime
      conversionId
      conversionStatus
      utmContent
      device
      orders {{
        orderId
        orderStatus
        items {{
          shopId
          completeTime
          modelId
          itemId
          itemName
          itemPrice
          displayItemStatus
          actualAmount
          refundAmount
          qty
          imageUrl
          itemCommission
          itemTotalCommission
          channelType
        }}
      }}
    }}
    pageInfo {{
      hasNextPage
      scrollId
    }}
  }}
}}
"""


class ShopeeProvider:
    """Implementa ProductProvider e LinkProvider sobre a API oficial."""

    name = SOURCE_SHOPEE
    is_demo = False
    conversion_window_days = MAX_CONVERSION_WINDOW_DAYS

    def __init__(
        self,
        client: ShopeeClient,
        *,
        now: Callable[[], datetime] = utcnow,
    ) -> None:
        self._client = client
        self._now = now

    def search_products(self, query: ProductQuery) -> ProductPage:
        self._validate_query(query)
        sort_type = SORT_TYPES[query.sort]

        variables: dict[str, object] = {
            "page": query.page,
            "limit": query.page_size,
            "sortType": sort_type,
        }
        if query.keyword:
            variables["keyword"] = query.keyword

        data = self._client.execute(_SEARCH_QUERY, variables)
        connection = data.get("productOfferV2") or {}
        if not isinstance(connection, dict):
            raise ProviderInvalidResponse(
                "A Shopee devolveu a busca em formato inesperado."
            )

        nodes = connection.get("nodes") or []
        if not isinstance(nodes, list):
            raise ProviderInvalidResponse(
                "A Shopee devolveu a lista de produtos em formato inesperado."
            )
        page_info = connection.get("pageInfo") or {}

        items = [self._map_node(node) for node in nodes]
        return ProductPage(
            items=items,
            page=query.page,
            page_size=query.page_size,
            has_next=bool(page_info.get("hasNextPage")),
            # A API não informa o total; inventar um número quebraria a tela.
            total=None,
        )

    def create_link(self, origin_url: str, sub_ids: tuple[str, ...]) -> GeneratedLink:
        origin_url = origin_url.strip()
        if not origin_url:
            raise ValidationError("A URL de origem é obrigatória.")
        if len(sub_ids) > MAX_SUB_IDS:
            raise ValidationError("São permitidos no máximo 5 Sub IDs.")

        payload: dict[str, object] = {"originUrl": origin_url}
        if sub_ids:
            payload["subIds"] = list(sub_ids)

        try:
            data = self._client.execute(
                _SHORT_LINK_MUTATION,
                {"input": payload},
                # Repetir a mutation pode criar dois links para o mesmo produto.
                retry=False,
            )
        except ProviderUnavailable as exc:
            raise ProviderUnavailable(
                "Não foi possível confirmar a geração do link. "
                "Verifique a lista antes de tentar novamente.",
                details=exc.details,
            ) from exc

        result = data.get("generateShortLink") or {}
        short_link = result.get("shortLink") if isinstance(result, dict) else None
        if not isinstance(short_link, str) or not short_link.strip():
            raise ProviderInvalidResponse("A Shopee não retornou um link válido.")

        return GeneratedLink(
            original_url=origin_url,
            affiliate_url=short_link.strip(),
            source=SOURCE_SHOPEE,
        )

    def fetch_conversions(self, query: ConversionQuery) -> list[ConversionRecord]:
        """Lê o Conversion Report inteiro da janela, página a página."""
        self._validate_conversion_query(query)
        start = _unix_seconds(query.start)
        end = _unix_seconds(query.end)
        query_text = _CONVERSION_QUERY.format(start=start, end=end)

        records: list[ConversionRecord] = []
        scroll_id = ""

        for _ in range(MAX_CONVERSION_PAGES):
            data = self._client.execute(
                query_text,
                {"limit": CONVERSION_PAGE_LIMIT, "scrollId": scroll_id},
            )
            page = _conversion_page(data)

            nodes = page.get("nodes") or []
            if not isinstance(nodes, list):
                raise ProviderInvalidResponse(
                    "A Shopee devolveu a lista de conversões em formato inesperado."
                )
            for node in nodes:
                records.extend(self._map_conversion_node(node))

            page_info = page.get("pageInfo") or {}
            if not isinstance(page_info, dict):
                raise ProviderInvalidResponse(
                    "A Shopee devolveu a paginação de conversões em formato inesperado."
                )
            if not page_info.get("hasNextPage"):
                return records

            next_scroll_id = page_info.get("scrollId")
            if not isinstance(next_scroll_id, str) or not next_scroll_id:
                raise ProviderInvalidResponse(
                    "A Shopee não retornou o cursor da próxima página de conversões."
                )
            scroll_id = next_scroll_id

        raise ProviderInvalidResponse(
            "A Shopee devolveu páginas demais para uma única sincronização."
        )

    def _validate_conversion_query(self, query: ConversionQuery) -> None:
        start = _as_naive_utc(query.start)
        end = _as_naive_utc(query.end)
        if start >= end:
            raise ValidationError("O início da janela precisa ser anterior ao fim.")

        now = _as_naive_utc(self._now())
        if end > now + timedelta(minutes=5):
            raise ValidationError("O fim da janela não pode estar no futuro.")
        if start < now - timedelta(
            days=MAX_CONVERSION_WINDOW_DAYS, minutes=5
        ):
            raise ValidationError(
                "A Shopee permite sincronizar apenas os últimos 90 dias."
            )

    @staticmethod
    def _map_conversion_node(node: object) -> list[ConversionRecord]:
        if not isinstance(node, dict):
            raise ProviderInvalidResponse(
                "A Shopee devolveu uma conversão em formato inesperado."
            )

        purchase_time = _timestamp(node.get("purchaseTime"))
        if purchase_time is None:
            raise ProviderInvalidResponse(
                "A Shopee devolveu uma conversão sem data de compra."
            )

        conversion_id = _integer(node.get("conversionId"))
        conversion_status = _optional_str(node.get("conversionStatus"))
        utm_content = _optional_str(node.get("utmContent"))
        device = _optional_str(node.get("device"))
        sub_ids = split_sub_ids(utm_content)
        # "ALL" é valor de filtro da API, não um dispositivo real.
        channel = None if (device or "").casefold() == "all" else device

        orders = node.get("orders") or []
        if not isinstance(orders, list):
            raise ProviderInvalidResponse(
                "A Shopee devolveu os pedidos da conversão em formato inesperado."
            )

        records: list[ConversionRecord] = []
        for order in orders:
            if not isinstance(order, dict):
                raise ProviderInvalidResponse(
                    "A Shopee devolveu um pedido em formato inesperado."
                )
            order_id = _optional_str(order.get("orderId"))
            if not order_id:
                raise ProviderInvalidResponse(
                    "A Shopee devolveu um pedido sem identificador."
                )
            if len(order_id) > MAX_ORDER_ID_LENGTH:
                raise ProviderInvalidResponse(
                    "A Shopee devolveu um pedido com identificador longo demais."
                )
            order_status = _optional_str(order.get("orderStatus"))

            items = order.get("items") or []
            if not isinstance(items, list):
                raise ProviderInvalidResponse(
                    "A Shopee devolveu os itens do pedido em formato inesperado."
                )
            for item in items:
                records.append(
                    ShopeeProvider._map_conversion_item(
                        item,
                        purchase_time=purchase_time,
                        order_id=order_id,
                        order_status=order_status,
                        conversion_id=conversion_id,
                        conversion_status=conversion_status,
                        utm_content=utm_content,
                        device=device,
                        channel=channel,
                        sub_ids=sub_ids,
                    )
                )
        return records

    @staticmethod
    def _map_conversion_item(
        item: object,
        *,
        purchase_time: datetime,
        order_id: str,
        order_status: str | None,
        conversion_id: int | None,
        conversion_status: str | None,
        utm_content: str | None,
        device: str | None,
        channel: str | None,
        sub_ids: tuple[str | None, ...],
    ) -> ConversionRecord:
        if not isinstance(item, dict):
            raise ProviderInvalidResponse(
                "A Shopee devolveu um item do pedido em formato inesperado."
            )

        item_id = _integer(item.get("itemId"))
        if item_id is None:
            raise ProviderInvalidResponse(
                "A Shopee devolveu um item sem identificador."
            )
        model_id = _integer(item.get("modelId")) or 0
        quantity = _integer(item.get("qty"))
        if quantity is None:
            # Mesma regra do CSV: linha de item sem quantidade explícita = 1.
            quantity = DEFAULT_QUANTITY
        if quantity < 0:
            raise ProviderInvalidResponse(
                "A Shopee devolveu uma quantidade inválida."
            )

        sales = _decimal(item.get("actualAmount"))
        if sales is None:
            price = _decimal(item.get("itemPrice"))
            sales = (price or Decimal(0)) * quantity
        commission = _decimal(item.get("itemTotalCommission"))
        if commission is None:
            commission = _decimal(item.get("itemCommission"))
        if commission is None:
            commission = Decimal(0)
        if sales < 0 or commission < 0:
            raise ProviderInvalidResponse(
                "A Shopee devolveu valores de venda ou comissão inválidos."
            )

        raw_status = (
            _optional_str(item.get("displayItemStatus"))
            or order_status
            or conversion_status
            or "unknown"
        )
        status = truncate_text(raw_status, MAX_STATUS_LENGTH) or "unknown"

        return ConversionRecord(
            external_order_id=order_id,
            external_item_id=item_id,
            shop_id=_integer(item.get("shopId")),
            title=truncate_text(
                _optional_str(item.get("itemName")), PRODUCT_TITLE_MAX_LENGTH
            ),
            image_url=_optional_str(item.get("imageUrl")),
            status=status,
            status_group=status_group_from_raw(raw_status),
            ordered_at=purchase_time,
            completed_at=_timestamp(item.get("completeTime")),
            quantity=quantity,
            sales_cents=_to_cents(sales),
            commission_cents=_to_cents(commission),
            sub_ids=sub_ids,
            channel=normalize_channel(channel),
            dedup_key=_order_dedup_key(order_id, item_id, model_id),
            source=SOURCE_SHOPEE,
            raw={
                "conversion_id": conversion_id,
                "conversion_status": conversion_status,
                "purchase_time": purchase_time.isoformat(),
                "utm_content": utm_content,
                "device": device,
                "order_id": order_id,
                "order_status": order_status,
                "item": item,
            },
        )

    def list_categories(self) -> list[str]:
        # A API expõe apenas IDs numéricos de categoria, sem catálogo de nomes.
        return []

    def _validate_query(self, query: ProductQuery) -> None:
        if query.page < 1:
            raise ValidationError("A página deve ser maior ou igual a 1.")
        if not 1 <= query.page_size <= MAX_PAGE_SIZE:
            raise ValidationError(
                f"O tamanho da página deve estar entre 1 e {MAX_PAGE_SIZE}.",
                details={"page_size": query.page_size},
            )
        if query.sort not in SORT_TYPES:
            raise ValidationError(
                "O provedor oficial não permite esta ordenação.",
                details={"sort": query.sort},
            )
        if query.category:
            raise ValidationError(
                "O provedor oficial não permite filtrar por categoria."
            )
        if (
            query.price_min_cents is not None
            or query.price_max_cents is not None
        ):
            raise ValidationError(
                "O provedor oficial não permite filtrar por preço."
            )
        if query.min_commission_rate_bp is not None:
            raise ValidationError(
                "O provedor oficial não permite filtrar por comissão mínima."
            )

    @staticmethod
    def _map_node(node: object) -> ProductRecord:
        if not isinstance(node, dict):
            raise ProviderInvalidResponse(
                "A Shopee devolveu um produto em formato inesperado."
            )

        item_id = _integer(node.get("itemId"))
        shop_id = _integer(node.get("shopId"))
        title = node.get("productName")
        product_url = node.get("productLink")
        if item_id is None or shop_id is None or not title or not product_url:
            raise ProviderInvalidResponse(
                "A Shopee devolveu um produto sem os campos obrigatórios."
            )

        price = _decimal(node.get("price"))
        if price is None:
            price = _decimal(node.get("priceMin"))
        commission = _decimal(node.get("commissionRate"))
        if price is None or commission is None:
            raise ProviderInvalidResponse(
                "A Shopee devolveu um produto sem preço ou comissão."
            )
        if price < 0 or commission < 0 or commission > 1:
            raise ProviderInvalidResponse(
                "A Shopee devolveu valores fora do intervalo esperado."
            )

        sales = _integer(node.get("sales"))
        rating = _decimal(node.get("ratingStar"))

        return ProductRecord(
            item_id=item_id,
            shop_id=shop_id,
            title=str(title)[:PRODUCT_TITLE_MAX_LENGTH],
            product_url=str(product_url),
            price_cents=_to_cents(price),
            commission_rate_bp=_to_basis_points(commission),
            image_url=_optional_str(node.get("imageUrl")),
            sales=sales,
            rating_x100=_to_x100(rating),
            # productCatIds são IDs; o modelo guarda nome de categoria.
            category=None,
            source=SOURCE_SHOPEE,
        )


def _decimal(value: object) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ProviderInvalidResponse(
            "A Shopee devolveu um valor numérico inválido."
        ) from exc


def _integer(value: object) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(str(value))
    except (TypeError, ValueError) as exc:
        raise ProviderInvalidResponse(
            "A Shopee devolveu um identificador inválido."
        ) from exc


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _to_cents(value: Decimal) -> int:
    return int((value * 100).to_integral_value(rounding=ROUND_HALF_UP))


def _to_basis_points(value: Decimal) -> int:
    return int((value * 10000).to_integral_value(rounding=ROUND_HALF_UP))


def _to_x100(value: Decimal | None) -> int | None:
    if value is None:
        return None
    return int((value * 100).to_integral_value(rounding=ROUND_HALF_UP))


def _conversion_page(data: dict[str, object]) -> dict[str, object]:
    page = data.get("conversionReport")
    if not isinstance(page, dict):
        raise ProviderInvalidResponse(
            "A Shopee devolveu o relatório de conversões em formato inesperado."
        )
    return page


def _timestamp(value: object) -> datetime | None:
    """Converte segundos Unix em UTC sem timezone; zero significa ausência."""
    if value is None or value == "":
        return None
    try:
        seconds = int(str(value))
    except (TypeError, ValueError) as exc:
        raise ProviderInvalidResponse(
            "A Shopee devolveu uma data inválida."
        ) from exc
    if seconds <= 0:
        return None
    try:
        return datetime.fromtimestamp(seconds, tz=timezone.utc).replace(tzinfo=None)
    except (OverflowError, OSError, ValueError) as exc:
        raise ProviderInvalidResponse(
            "A Shopee devolveu uma data fora do intervalo esperado."
        ) from exc


def _as_naive_utc(value: datetime) -> datetime:
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def _unix_seconds(value: datetime) -> int:
    aware = _as_naive_utc(value).replace(tzinfo=timezone.utc)
    return int(aware.timestamp())


def _order_dedup_key(order_id: str, item_id: int, model_id: int) -> str:
    digest = hashlib.sha256(
        f"{order_id}|{item_id}|{model_id}".encode("utf-8")
    ).hexdigest()
    return f"order:{digest}"

