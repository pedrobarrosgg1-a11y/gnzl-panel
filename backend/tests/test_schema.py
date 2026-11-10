"""Testes de integridade do esquema criado pelas migrations.

Cada teste aqui representa uma regra que o banco recusa violar. Se um deles
falhar, a integridade dos dados depende só de código de aplicação — o que não
é suficiente para histórico de links e comissões.
"""

from datetime import datetime

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import PROJECT_ROOT
from app.database.session import create_db_engine
from app.models import (
    AffiliateLink,
    LinkBatch,
    LinkBatchItem,
    Product,
    ProductList,
    ProductListItem,
    SubIdValue,
)

MIGRATIONS_DIR = PROJECT_ROOT / "backend" / "migrations"

EXPECTED_TABLES = {
    "affiliate_links",
    "alembic_version",
    "link_batch_items",
    "link_batches",
    "product_list_items",
    "product_lists",
    "products",
    "sub_id_values",
}


def _product(session: Session, *, item_id: int = 1, shop_id: int = 10) -> Product:
    product = Product(
        item_id=item_id,
        shop_id=shop_id,
        title="Fone bluetooth",
        price_cents=19990,
        commission_rate_bp=850,
        data_source="demo",
    )
    session.add(product)
    session.flush()
    return product


def test_migration_creates_all_phase_one_tables(engine) -> None:
    assert set(inspect(engine).get_table_names()) == EXPECTED_TABLES


def test_migration_upgrade_downgrade_upgrade(database_url: str) -> None:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", database_url)

    command.downgrade(config, "base")
    command.upgrade(config, "head")

    engine = create_db_engine(database_url)
    try:
        assert set(inspect(engine).get_table_names()) == EXPECTED_TABLES
    finally:
        engine.dispose()


def test_product_identity_is_unique_per_source(session: Session) -> None:
    _product(session, item_id=1, shop_id=10)
    session.add(
        Product(
            item_id=1,
            shop_id=10,
            title="Mesmo produto",
            price_cents=100,
            commission_rate_bp=100,
            data_source="demo",
        )
    )

    with pytest.raises(IntegrityError):
        session.commit()


def test_same_item_can_exist_in_demo_and_shopee(session: Session) -> None:
    _product(session, item_id=1, shop_id=10)
    session.add(
        Product(
            item_id=1,
            shop_id=10,
            title="Mesmo produto real",
            price_cents=100,
            commission_rate_bp=100,
            data_source="shopee",
        )
    )

    session.commit()

    assert session.query(Product).count() == 2


def test_same_item_in_different_shop_is_allowed(session: Session) -> None:
    _product(session, item_id=1, shop_id=10)
    _product(session, item_id=1, shop_id=20)

    session.commit()

    assert session.query(Product).count() == 2


def test_list_item_requires_existing_product(session: Session) -> None:
    product_list = ProductList(name="Black Friday", normalized_name="black-friday")
    session.add(product_list)
    session.flush()

    session.add(ProductListItem(product_list_id=product_list.id, product_id=999))

    with pytest.raises(IntegrityError):
        session.commit()


def test_duplicate_product_in_same_list_is_rejected(session: Session) -> None:
    product = _product(session)
    product_list = ProductList(name="Stories", normalized_name="stories")
    session.add(product_list)
    session.flush()
    session.add(ProductListItem(product_list_id=product_list.id, product_id=product.id))
    session.commit()

    session.add(ProductListItem(product_list_id=product_list.id, product_id=product.id))

    with pytest.raises(IntegrityError):
        session.commit()


def test_deleting_list_removes_its_items_but_keeps_products(session: Session) -> None:
    product = _product(session)
    product_list = ProductList(name="Verão", normalized_name="verao")
    session.add(product_list)
    session.flush()
    session.add(ProductListItem(product_list_id=product_list.id, product_id=product.id))
    session.commit()

    session.delete(product_list)
    session.commit()

    assert session.query(ProductListItem).count() == 0
    assert session.query(Product).count() == 1


def test_list_batch_requires_list_when_destination_is_list(session: Session) -> None:
    session.add(
        LinkBatch(destination_type="list", total_items=1, data_source="demo")
    )

    with pytest.raises(IntegrityError):
        session.commit()


def test_product_batch_must_not_reference_list(session: Session) -> None:
    product_list = ProductList(name="Lista", normalized_name="lista")
    session.add(product_list)
    session.flush()

    session.add(
        LinkBatch(
            destination_type="product",
            product_list_id=product_list.id,
            total_items=1,
            data_source="demo",
        )
    )

    with pytest.raises(IntegrityError):
        session.commit()


def test_batch_counters_cannot_exceed_total(session: Session) -> None:
    session.add(
        LinkBatch(
            destination_type="product",
            total_items=1,
            successful_items=1,
            failed_items=1,
            data_source="demo",
        )
    )

    with pytest.raises(IntegrityError):
        session.commit()


def test_successful_item_requires_affiliate_link(session: Session) -> None:
    batch = LinkBatch(destination_type="product", total_items=1, data_source="demo")
    session.add(batch)
    session.flush()

    session.add(
        LinkBatchItem(
            link_batch_id=batch.id,
            original_url="https://shopee.com.br/x-i.1.2",
            status="success",
        )
    )

    with pytest.raises(IntegrityError):
        session.commit()


def test_affiliate_url_is_unique(session: Session) -> None:
    product = _product(session)
    for _ in range(2):
        session.add(
            AffiliateLink(
                product_id=product.id,
                original_url="https://shopee.com.br/x-i.1.2",
                affiliate_url="https://shope.ee/abc123",
                data_source="demo",
            )
        )

    with pytest.raises(IntegrityError):
        session.commit()


def test_sub_ids_are_stored_only_in_canonical_form(session: Session) -> None:
    product = _product(session)
    session.commit()

    session.add(
        AffiliateLink(
            product_id=product.id,
            original_url="https://shopee.com.br/x-i.1.2",
            affiliate_url="https://shope.ee/invalido",
            sub_id_1="Instagram",
            data_source="demo",
        )
    )

    with pytest.raises(IntegrityError):
        session.commit()

    session.rollback()
    session.add(
        AffiliateLink(
            product_id=product.id,
            original_url="https://shopee.com.br/x-i.1.2",
            affiliate_url="https://shope.ee/valido",
            sub_id_1="instagram",
            sub_id_2="stories",
            data_source="demo",
        )
    )
    session.commit()

    assert session.query(AffiliateLink).count() == 1


def test_product_with_links_cannot_be_deleted(session: Session) -> None:
    product = _product(session)
    session.add(
        AffiliateLink(
            product_id=product.id,
            original_url="https://shopee.com.br/x-i.1.2",
            affiliate_url="https://shope.ee/abc123",
            data_source="demo",
        )
    )
    session.commit()

    session.delete(product)

    with pytest.raises(IntegrityError):
        session.commit()


def test_sub_id_value_keeps_one_row_per_dimension_and_value(session: Session) -> None:
    session.add(
        SubIdValue(
            dimension="sub_id_1",
            normalized_value="instagram",
            display_value="Instagram",
            last_used_at=datetime(2026, 11, 9, 12, 0, 0),
        )
    )
    session.commit()

    session.add(
        SubIdValue(
            dimension="sub_id_1",
            normalized_value="instagram",
            display_value="instagram",
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

    # O mesmo valor em outra dimensão é permitido.
    session.add(
        SubIdValue(
            dimension="sub_id_2",
            normalized_value="instagram",
            display_value="instagram",
        )
    )
    session.commit()

    assert session.query(SubIdValue).count() == 2


def test_foreign_keys_are_enforced_per_connection(engine) -> None:
    with engine.connect() as connection:
        assert connection.execute(text("PRAGMA foreign_keys")).scalar() == 1
