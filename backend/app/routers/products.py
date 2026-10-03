from typing import Annotated

from fastapi import APIRouter, Path, Query

from app.core.dependencies import DatabaseSession
from app.models import Product
from app.schemas.product import ProductResponse
from app.services import products as product_service

router = APIRouter(prefix="/api/products", tags=["Products"])


@router.get("", response_model=list[ProductResponse])
def list_products(
    db: DatabaseSession,
    skip: Annotated[int, Query(ge=0, le=2_147_483_647)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[Product]:
    return product_service.list_products(db, skip, limit)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: Annotated[int, Path(ge=1, le=2_147_483_647)], db: DatabaseSession
) -> Product:
    return product_service.get_product(db, product_id)
