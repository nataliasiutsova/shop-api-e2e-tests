from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from datetime import datetime


class ProductBase(BaseModel):

    model_config = ConfigDict( extra="forbid", str_strip_whitespace=True)

    name: str = Field( min_length=1, max_length=255 )
    description: str | None = Field(default=None, max_length=2000)
    category: str = Field( min_length=1, max_length=100 )
    price: float = Field( gt=0, le=1000 )
    stock: int = Field(default=0, ge=0, le=100)
    image_url: HttpUrl | None = None
    # rating: float = Field( ge=0, le=5 )
    # reviews_count: int = Field( ge=0 )
    # created_at: datetime | None = None
    # updated_at: datetime | None = None


class ProductCreate(ProductBase):
    #Payload for POST / products.
    pass

class ProductUpdate(BaseModel):
    #Payload for PUT / products / {id}.

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1, max_length=2000)
    price: float | None = Field(default=None, gt=0, le=1000)
    stock: int | None = Field(default=None, ge=0, le=100)


class ProductResponse(ProductBase):

    id: int = Field(gt=0)
    rating: float| None = Field( ge=0, le=5)
    reviews_count: int| None = Field(ge=0)
    created_at: datetime | None = Field(default=None)
    updated_at: datetime | None = Field(default=None)