"""Schemas de produtos."""

from pydantic import BaseModel

from app.models.product import Product


class ProductOut(BaseModel):
    """Produto como o frontend recebe. Valores em centavos, sem formatação."""

    id: int
    item_id: int
    shop_id: int
    title: str
    image_url: str | None
    product_url: str | None
    price_cents: int
    commission_rate_bp: int
    sales: int | None
    rating_x100: int | None
    category: str | None
    source: str

    @classmethod
    def from_model(cls, product: Product) -> "ProductOut":
        return cls(
            id=product.id,
            item_id=product.item_id,
            shop_id=product.shop_id,
            title=product.title,
            image_url=product.image_url,
            product_url=product.product_url,
            price_cents=product.price_cents,
            commission_rate_bp=product.commission_rate_bp,
            sales=product.sales,
            rating_x100=product.rating_x100,
            category=product.category,
            source=product.data_source,
        )


class ProductSearchResponse(BaseModel):
    items: list[ProductOut]
    page: int
    page_size: int
    has_next: bool
    total: int | None
    source: str
    is_demo: bool


class CategoriesResponse(BaseModel):
    items: list[str]
    source: str
    is_demo: bool
