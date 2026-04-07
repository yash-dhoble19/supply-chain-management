from pydantic import BaseModel
from typing import Optional


class InventoryItem(BaseModel):
    id: int
    sku: str
    name: str
    category: str
    stage: str
    stock: int
    safety_stock_level: int
    optimal_stock_level: int
    unit_price: float
    status: str
    capacity: float
    pending_po_qty: int
    in_transit_po_qty: int
    total_value: float


class InventorySummary(BaseModel):
    total_items: int
    total_value: float
    critical_items: int


class InventoryAdjustment(BaseModel):
    target_stock: Optional[int] = None
    quantity_change: Optional[int] = None
    reason: str


class InventoryActivityItem(BaseModel):
    id: int
    product_id: int
    product_name: str
    sku: str
    change_date: str
    quantity_change: int
    reason: str
    stockout_flag: bool
