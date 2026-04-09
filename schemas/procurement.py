from pydantic import BaseModel
from typing import Optional


class SupplierWrite(BaseModel):
    supplier_name: str
    email: str
    company_name: Optional[str] = None
    supplier_code: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None

    product_name: Optional[str] = None
    product_category: Optional[str] = None
    unit_price: float = 0.0
    currency: str = "USD"
    delivery_cost: float = 0.0
    average_delivery_days: int = 5
    minimum_order_quantity: Optional[int] = None

    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None

    supplier_type: str = "Strategic"
    status: str = "ACTIVE"
    preferred_supplier: bool = False
    supplier_score: Optional[float] = None
    reliability_percent: float = 95.0
    on_time_delivery_percent: float = 93.5

    gst_number: Optional[str] = None
    tax_id: Optional[str] = None
    notes: Optional[str] = None


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

# anything
