from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict


class OrderItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int = Field(gt=0)
    created_at: datetime
    price: float = Field(gt=0, le=1000)
    product_id: int = Field(gt=0)
    product_name: str = Field(min_length=1, max_length=255)
    quantity: int = Field(ge=1, le=100)
    total: float = Field(gt=0)


class OrderResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int = Field(gt=0)
    created_at: datetime
    updated_at: datetime | None = Field(default=None)
    items: list[OrderItem]
    status: Literal["pending", "cancelled"]
    total: float = Field(gt=0)


class OrderCancelResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int = Field(gt=0)
    created_at: datetime
    updated_at: datetime
    items: list[OrderItem]
    status: Literal["cancelled"]
    total: float = Field(gt=0)
