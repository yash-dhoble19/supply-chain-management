from pydantic import BaseModel
from typing import List, Optional


class RouteRequest(BaseModel):
    start_address: str
    end_address: str
    waypoints: List[str] = []


class CarrierCreate(BaseModel):
    name: str
    contact_info: Optional[str] = None
    fleet_size: int = 1
    rating: float = 4.5


class DriverCreate(BaseModel):
    name: str
    license_number: str
    status: str = "AVAILABLE"
    carrier_id: int


class ShipmentCreate(BaseModel):
    tracking_number: str
    origin: str
    destination: str
    carrier_id: Optional[int] = None
    driver_id: Optional[int] = None
    waypoints: List[str] = []
    scheduled_date: Optional[str] = None  # ISO format string


class ShipmentUpdate(BaseModel):
    status: Optional[str] = None
    current_location_lat: Optional[float] = None
    current_location_lon: Optional[float] = None
    progress_percent: Optional[float] = None
