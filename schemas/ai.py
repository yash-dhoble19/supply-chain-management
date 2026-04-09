from pydantic import BaseModel
from typing import List


class AIProductParseRequest(BaseModel):
    description: str


class PricingRequest(BaseModel):
    product_name: str
    current_price: float
    current_stock: int
    optimal_stock: int
    category: str


class InventoryReportRequest(BaseModel):
    products: List[dict]


class SimulationRequest(BaseModel):
    scenario: str
    products: List[dict]


class ReorderRequest(BaseModel):
    product_name: str
    supplier_name: str = "Valued Supplier"
    current_stock: int
    optimal_stock: int
    unit_price: float


class AgentRouteRequest(BaseModel):
    intent: str
    payload: dict

# anything
