from pydantic import BaseModel
from typing import Optional


class ProductCreate(BaseModel):
    sku: str
    name: str
    category: str
    stage: str
    current_stock: int
    safety_stock_level: int
    optimal_stock_level: int
    unit_price: float


class ProductUpdate(BaseModel):
    sku: Optional[str] = None
    name: Optional[str] = None
    category: Optional[str] = None
    stage: Optional[str] = None
    current_stock: Optional[int] = None
    safety_stock_level: Optional[int] = None
    optimal_stock_level: Optional[int] = None
    unit_price: Optional[float] = None


class StockMovement(BaseModel):
    product_id: int
    quantity_change: int
    reason: str
