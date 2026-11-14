"""Equivalência de normalização entre o CSV canônico e o provedor Shopee.

As duas origens gravam na mesma tabela e alimentam o mesmo dashboard. Este
teste percorre os dois caminhos com o mesmo pedido e exige campos idênticos:
se uma regra mudar em um lado só, ele quebra.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.conversion import Order
from app.providers.shopee.provider import ShopeeProvider
from app.services.csv_import import CsvImportService

ORDER_HEADER = (
    "order_id,item_id,shop_id,status,status_group,ordered_at,quantity,"
    "sales_cents,commission_cents,sub_id_1,sub_id_2,channel,title,image_url,"
    "completed_at"
)

PURCHASE_TIME = datetime(2026, 11, 1, 10, 0)
COMPLETE_TIME = datetime(2026, 11, 2, 10, 0)

_COMPARED_FIELDS = (
    "external_order_id",
    "external_item_id",
    "shop_id",
    "title",
    "image_url",
    "status",
    "status_group",
    "ordered_at",
    "completed_at",
    "quantity",
    "sales_cents",
    "commission_cents",
    "channel",
)


def _epoch(value: datetime) -> int:
    return int(value.replace(tzinfo=timezone.utc).timestamp())


def _shopee_record():
    node = {
        "conversionId": 1,
        "conversionStatus": "COMPLETED",
        "purchaseTime": _epoch(PURCHASE_TIME),
        "utmContent": "Campanha, Banner",
        "device": "app",
        "orders": [
            {
                "orderId": "260101ABCDEF",
                "orderStatus": "COMPLETED",
                "items": [
                    {
                        "itemId": 14888686365,
                        "shopId": 573579437,
                        "modelId": 0,
                        "itemName": "Fone bluetooth",
                        "imageUrl": "https://img.example/x.jpg",
                        "qty": 2,
                        "actualAmount": "199.90",
                        "itemTotalCommission": "17.00",
                        "completeTime": _epoch(COMPLETE_TIME),
                        "displayItemStatus": "Aprovado",
                    }
                ],
            }
        ],
    }
    return ShopeeProvider._map_conversion_node(node)[0]


def _csv_order(session: Session) -> Order:
    content = "\n".join(
        [
            ORDER_HEADER,
            (
                "260101ABCDEF,14888686365,573579437,Aprovado,,"
                "2026-11-01T10:00:00,2,19990,1700,Campanha,Banner,app,"
                "Fone bluetooth,https://img.example/x.jpg,2026-11-02T10:00:00"
            ),
        ]
    ).encode("utf-8")

    CsvImportService(session).import_orders("conversion.csv", content)
    return session.query(Order).one()


def test_csv_and_shopee_store_the_same_normalized_fields(session: Session) -> None:
    order = _csv_order(session)
    record = _shopee_record()

    for field in _COMPARED_FIELDS:
        assert getattr(record, field) == getattr(order, field), field

    assert record.sub_ids == (
        order.sub_id_1,
        order.sub_id_2,
        order.sub_id_3,
        order.sub_id_4,
        order.sub_id_5,
    )
    assert record.sub_ids == ("campanha", "banner", None, None, None)
    assert record.status_group == "approved"
    assert record.channel == "APP"
