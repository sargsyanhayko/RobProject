from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Path, UploadFile, status

from app.core.dependencies import DatabaseSession, get_current_admin
from app.models import Product
from app.schemas.product import (
    ProductCategory,
    ProductCreate,
    ProductPrice,
    ProductResponse,
    ProductTitle,
    ProductUpdate,
)
from app.services import products as product_service
from app.services.images import read_product_image

router = APIRouter(
    prefix="/api/admin/products",
    tags=["Admin products"],
    dependencies=[Depends(get_current_admin)],
)
ProductID = Annotated[int, Path(ge=1, le=2_147_483_647)]
ProductPhoto = Annotated[
    UploadFile,
    File(
        description="JPEG, PNG, WebP or GIF; up to 5 MB",
        json_schema_extra={"format": "binary"},
    ),
]


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(data: ProductCreate, db: DatabaseSession) -> Product:
    return product_service.create_product(db, data)


@router.post(
    "/upload", response_model=ProductResponse, status_code=status.HTTP_201_CREATED
)
def create_product_with_image(
    db: DatabaseSession,
    title: Annotated[ProductTitle, Form()],
    price: Annotated[ProductPrice, Form()],
    category: Annotated[ProductCategory, Form()],
    file: ProductPhoto,
    description: Annotated[str | None, Form()] = None,
) -> Product:
    """Create a product and store its uploaded photo in one database transaction."""
    data = ProductCreate(
        title=title, price=price, category=category, description=description
    )
    image = read_product_image(file)
    return product_service.create_product(db, data, image)


@router.patch("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: ProductID, data: ProductUpdate, db: DatabaseSession
) -> Product:
    """Update provided fields; null clears description and image_url."""
    return product_service.update_product(db, product_id, data)


@router.patch("/{product_id}/upload", response_model=ProductResponse)
def update_product_with_image(
    product_id: ProductID,
    db: DatabaseSession,
    title: Annotated[ProductTitle, Form()],
    price: Annotated[ProductPrice, Form()],
    file: ProductPhoto,
    description: Annotated[str | None, Form()] = None,
    category: Annotated[ProductCategory | None, Form()] = None,
) -> Product:
    """Save the form fields and replace the photo in one database transaction."""
    data = ProductUpdate(title=title, price=price, description=description)
    if category is not None:
        data.category = category
    image = read_product_image(file)
    return product_service.update_product(db, product_id, data, image)


@router.delete("/{product_id}")
def delete_product(product_id: ProductID, db: DatabaseSession) -> dict[str, str]:
    product_service.delete_product(db, product_id)
    return {"message": "Product deleted"}
