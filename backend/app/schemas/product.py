from datetime import datetime
from decimal import Decimal
from typing import Annotated, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_serializer,
    model_validator,
)

ProductTitle = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)
]
ProductPrice = Annotated[
    Decimal, Field(ge=0, max_digits=12, decimal_places=2, allow_inf_nan=False)
]
ProductImageURL = Annotated[str, StringConstraints(max_length=1000)]


class ProductCreate(BaseModel):
    title: ProductTitle
    description: str | None = None
    price: ProductPrice
    image_url: ProductImageURL | None = None


class ProductUpdate(BaseModel):
    title: ProductTitle | None = None
    description: str | None = None
    price: ProductPrice | None = None
    image_url: ProductImageURL | None = None

    @model_validator(mode="after")
    def reject_null_required_fields(self) -> Self:
        # Omitted fields stay unchanged; only nullable columns can be cleared.
        for name in ("title", "price"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        return self


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    price: Decimal
    image_url: str | None
    created_at: datetime
    updated_at: datetime

    @field_serializer("price", when_used="json")
    def serialize_price(self, value: Decimal) -> str:
        return format(value, ".2f")
