from pydantic import BaseModel
from typing import Optional


class SupplierCreate(BaseModel):
    name: str
    contact_email: str
    category: str
    reliability_score: float = 95.0
    delivery_speed_days: int = 5
    price_per_unit: float = 10.0


class POCreate(BaseModel):
    supplier_id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    priority: str = "Medium"


class QuickPOCreate(BaseModel):
    insightId: str
    sku: str
    itemName: str
    unitPrice: float
    quantity: int
    supplierName: str
    estimatedLeadTime: Optional[str] = None
    supplierId: Optional[int] = None
    productId: Optional[int] = None
    priority: str = "High"
    notes: Optional[str] = None


class POStatusUpdate(BaseModel):
    status: str


class ProcurementRequest(BaseModel):
    material_name: str
    quantity: int
    max_days_allowed: int
