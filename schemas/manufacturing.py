from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional
from datetime import date
from decimal import Decimal


class ManufacturingGoodsBase(BaseModel):
    sku: str
    product_name: str
    status: Optional[str] = "Pending"
    progress: Optional[int] = 0
    start_date: Optional[date] = None
    est_completion: Optional[date] = None
    unit_price: float

    @field_validator('unit_price', mode='before')
    @classmethod
    def convert_unit_price(cls, v):
        if isinstance(v, Decimal):
            return float(v)
        return v


class ManufacturingGoodsCreate(ManufacturingGoodsBase):
    pass


class ManufacturingGoodsUpdate(BaseModel):
    status: Optional[str] = None
    progress: Optional[int] = None


class ManufacturingGoods(ManufacturingGoodsBase):
    id: int

    model_config = ConfigDict(from_attributes=True, extra='ignore')
# anything
