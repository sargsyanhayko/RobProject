from typing import Annotated

from fastapi import APIRouter, Depends, Path, status

from app.core.dependencies import DatabaseSession, get_current_admin
from app.models import Product
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services import products as product_service

router = APIRouter(
    prefix="/api/admin/products",
    tags=["Admin products"],
    dependencies=[Depends(get_current_admin)],
)
ProductID = Annotated[int, Path(ge=1, le=2_147_483_647)]


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(data: ProductCreate, db: DatabaseSession) -> Product:
    return product_service.create_product(db, data)


@router.patch("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: ProductID, data: ProductUpdate, db: DatabaseSession
) -> Product:
    """Update provided fields; null clears description and image_url."""
    return product_service.update_product(db, product_id, data)


@router.delete("/{product_id}")
def delete_product(product_id: ProductID, db: DatabaseSession) -> dict[str, str]:
    product_service.delete_product(db, product_id)
    return {"message": "Product deleted"}
