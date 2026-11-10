"""Catálogo fictício do modo demonstração.

Os produtos existem apenas para exercitar a aplicação sem a Open API. Todos
têm ``source='demo'`` e a interface sinaliza isso. Nenhum dado aqui representa
preço, venda ou comissão real da Shopee.
"""

import unicodedata

from app.providers.base import SOURCE_DEMO, ProductRecord

DEMO_FAILING_ITEM_ID = 999_999_999

# title, categoria, preço em centavos, comissão em bp, vendas, avaliação x100
_RAW: tuple[tuple[str, str, int, int, int | None, int | None], ...] = (
    ("Fone bluetooth com cancelamento de ruído", "Eletrônicos", 12990, 1200, 4820, 470),
    ("Smartwatch com monitor cardíaco", "Eletrônicos", 24990, 900, 2130, 460),
    ("Caixa de som portátil à prova d'água", "Eletrônicos", 8990, 1000, 7640, 450),
    ("Carregador turbo 65W USB-C", "Eletrônicos", 4590, 700, 12300, 480),
    ("Teclado mecânico compacto", "Eletrônicos", 21990, 800, 980, 490),
    ("Webcam full HD com microfone", "Eletrônicos", 17990, 650, 640, 440),
    ("Suporte articulado para notebook", "Eletrônicos", 5990, 1100, 3310, None),
    ("Air fryer 5 litros digital", "Casa", 39990, 700, 5420, 470),
    ("Jogo de panelas antiaderentes 5 peças", "Casa", 18990, 950, 1870, 450),
    ("Luminária de mesa com três temperaturas", "Casa", 4590, 1200, 2960, 460),
    ("Organizador modular de gaveta", "Casa", 2490, 1300, 8730, 430),
    ("Cafeteira elétrica programável", "Casa", 27990, 800, 1150, 440),
    ("Purificador de água de bancada", "Casa", 54990, 500, 420, 480),
    ("Aspirador vertical sem fio", "Casa", 42990, 600, 890, 450),
    ("Kit skincare com ácido hialurônico", "Beleza", 8990, 1500, 4210, 470),
    ("Secador de cabelo profissional", "Beleza", 19990, 900, 1680, 460),
    ("Escova secadora modeladora", "Beleza", 15990, 1000, 5720, 440),
    ("Perfume floral feminino 100ml", "Beleza", 22990, 1100, 2340, None),
    ("Máscara capilar de reconstrução", "Beleza", 3490, 1400, 9820, 480),
    ("Tênis de corrida leve", "Moda", 17990, 800, 3150, 450),
    ("Mochila impermeável para notebook", "Moda", 12990, 1000, 2480, 470),
    ("Óculos de sol polarizados", "Moda", 7990, 1200, 1360, None),
    ("Relógio minimalista com pulseira de aço", "Moda", 24990, 700, 740, 440),
    ("Garrafa térmica 1 litro", "Esporte", 4990, 900, 6180, 490),
    ("Kit halteres ajustáveis 20kg", "Esporte", 15990, 800, 510, 450),
    ("Tapete de yoga antiderrapante", "Esporte", 6990, 1000, 2240, 460),
    ("Parafusadeira sem fio com maleta", "Ferramentas", 24990, 600, 1320, 470),
    ("Kit de chaves combinadas 12 peças", "Ferramentas", 9990, 900, 860, 440),
    ("Comedouro automático para pets", "Pet", 5990, 1100, 3470, 450),
    ("Cama pet acolchoada tamanho M", "Pet", 12990, 1000, 1590, 470),
)


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii").lower()
    return "-".join(part for part in ascii_only.replace("'", "").split() if part)


def _build_catalog() -> tuple[ProductRecord, ...]:
    records: list[ProductRecord] = []
    for index, (title, category, price, commission, sales, rating) in enumerate(_RAW):
        item_id = 100_000 + index * 137
        shop_id = 5_000 + index % 7
        records.append(
            ProductRecord(
                item_id=item_id,
                shop_id=shop_id,
                title=title,
                product_url=f"https://shopee.com.br/{_slugify(title)}-i.{shop_id}.{item_id}",
                price_cents=price,
                commission_rate_bp=commission,
                sales=sales,
                rating_x100=rating,
                category=category,
                source=SOURCE_DEMO,
            )
        )

    records.append(
        ProductRecord(
            item_id=DEMO_FAILING_ITEM_ID,
            shop_id=9_000,
            title="Produto de demonstração com falha simulada",
            product_url=f"https://shopee.com.br/produto-com-falha-i.9000.{DEMO_FAILING_ITEM_ID}",
            price_cents=9990,
            commission_rate_bp=1000,
            sales=10,
            rating_x100=300,
            category="Ferramentas",
            source=SOURCE_DEMO,
        )
    )
    return tuple(records)


DEMO_PRODUCTS: tuple[ProductRecord, ...] = _build_catalog()
