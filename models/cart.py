from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class CartItemBase(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    product_id: int = Field(gt=0)
    quantity: int = Field(ge=1, le=100)


class CartItemCreate(CartItemBase):
    """Payload for POST /cart/items."""
    pass


class CartItemUpdate(BaseModel):
    """Payload for PUT /cart/items/{id}."""

    model_config = ConfigDict(extra="forbid")

    quantity: int = Field(ge=1, le=100)


class CartItemResponse(CartItemBase):
    id: int = Field(gt=0)
    price: float = Field(gt=0, le=1000)
    product_name: str = Field(min_length=1, max_length=255)
    total: float = Field(gt=0)
    created_at: datetime | None = Field(default=None)


class CartResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    count: int = Field(ge=0)
    items: list[CartItemResponse]
    total: float = Field(ge=0)
