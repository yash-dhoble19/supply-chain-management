from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PublishedGoodsBase(BaseModel):
    product_id: int
    sku: str
    name: str
    category: str
    unit_price: float
    image_url: Optional[str] = None
    supplier_name: Optional[str] = None
    notes: Optional[str] = None

class PublishedGoodsCreate(PublishedGoodsBase):
    pass

class PublishedGoodsOut(PublishedGoodsBase):
    id: int
    published_at: datetime

    class Config:
        orm_mode = True
