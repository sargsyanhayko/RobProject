from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Product
from app.schemas.product import ProductCategory, ProductCreate, ProductUpdate
from app.services.images import ProductImage


def list_products(
    db: Session, skip: int, limit: int, category: ProductCategory | None = None
) -> list[Product]:
    statement = select(Product)
    if category is not None:
        statement = statement.where(Product.category == category)
    statement = statement.order_by(Product.id).offset(skip).limit(limit)
    return list(db.scalars(statement).all())


def get_product(db: Session, product_id: int) -> Product:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )
    return product


def create_product(
    db: Session, data: ProductCreate, image: ProductImage | None = None
) -> Product:
    product = Product(**data.model_dump())
    db.add(product)
    if image is not None:
        db.flush()
        _set_product_image(product, image)
    db.commit()
    db.refresh(product)
    return product


def update_product(
    db: Session,
    product_id: int,
    data: ProductUpdate,
    image: ProductImage | None = None,
) -> Product:
    product = get_product(db, product_id)
    changes = data.model_dump(exclude_unset=True)
    if "image_url" in changes and changes["image_url"] != product.image_url:
        product.image_data = None
        product.image_content_type = None
    for name, value in changes.items():
        setattr(product, name, value)
    if image is not None:
        _set_product_image(product, image)
    db.commit()
    db.refresh(product)
    return product


def _set_product_image(product: Product, image: ProductImage) -> None:
    product.image_data = image.data
    product.image_content_type = image.content_type
    product.image_url = f"/api/products/{product.id}/image"


def get_product_image(db: Session, product_id: int) -> ProductImage:
    product = get_product(db, product_id)
    if product.image_data is None or product.image_content_type is None:
        raise HTTPException(status_code=404, detail="Product image not found")
    return ProductImage(
        data=product.image_data, content_type=product.image_content_type
    )


def delete_product(db: Session, product_id: int) -> None:
    product = get_product(db, product_id)
    db.delete(product)
    db.commit()
