"""Provedor oficial de afiliados da Shopee (busca e geração de links)."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from app.core.constants import MAX_PAGE_SIZE, PRODUCT_TITLE_MAX_LENGTH
from app.core.errors import (
    ProviderInvalidResponse,
    ProviderUnavailable,
    ValidationError,
)
from app.providers.base import (
    SOURCE_SHOPEE,
    GeneratedLink,
    ProductPage,
    ProductQuery,
    ProductRecord,
)
from app.providers.shopee.client import ShopeeClient

MAX_SUB_IDS = 5

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


class ShopeeProvider:
    """Implementa ProductProvider e LinkProvider sobre a API oficial."""

    name = SOURCE_SHOPEE
    is_demo = False

    def __init__(self, client: ShopeeClient) -> None:
        self._client = client

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
