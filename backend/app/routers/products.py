from typing import Annotated

from fastapi import APIRouter, Path, Query, Response

from app.core.dependencies import DatabaseSession
from app.models import Product
from app.schemas.product import ProductCategory, ProductResponse
from app.services import products as product_service

router = APIRouter(prefix="/api/products", tags=["Products"])


@router.get("", response_model=list[ProductResponse])
def list_products(
    db: DatabaseSession,
    skip: Annotated[int, Query(ge=0, le=2_147_483_647)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    category: Annotated[ProductCategory | None, Query()] = None,
) -> list[Product]:
    return product_service.list_products(db, skip, limit, category)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: Annotated[int, Path(ge=1, le=2_147_483_647)], db: DatabaseSession
) -> Product:
    return product_service.get_product(db, product_id)


@router.get("/{product_id}/image", response_class=Response)
def get_product_image(
    product_id: Annotated[int, Path(ge=1, le=2_147_483_647)], db: DatabaseSession
) -> Response:
    image = product_service.get_product_image(db, product_id)
    return Response(
        content=image.data,
        media_type=image.content_type,
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )
