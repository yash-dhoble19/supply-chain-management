from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class OrderCreate(BaseModel):
    customer_name: str
    delivery_address: str
    order_source: str


class OrderResponse(BaseModel):
    id: int
    customer_name: str
    delivery_address: Optional[str] = None
    status: str
    ai_risk_assessment: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
