"""Garante que buscas concorrentes não colidem ao gravar o mesmo produto."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from sqlalchemy.orm import Session, sessionmaker

from app.database.session import create_db_engine
from app.models import Product
from app.providers.demo.catalog import DEMO_PRODUCTS
from app.repositories import products as products_repo


def test_concurrent_upsert_keeps_one_row_per_identity(database_url: str) -> None:
    engine = create_db_engine(database_url)
    factory = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    record = DEMO_PRODUCTS[0]
    barrier = Barrier(2)

    def upsert() -> None:
        barrier.wait()
        with factory() as session:
            products_repo.upsert_records(session, [record])
            session.commit()

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(lambda _: upsert(), range(2)))

        with Session(engine) as session:
            rows = session.query(Product).all()

        assert len(rows) == 1
        assert rows[0].item_id == record.item_id
    finally:
        engine.dispose()
