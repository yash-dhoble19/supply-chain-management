from typing import List, Optional

from pydantic import BaseModel, Field


class RoutePlanRequest(BaseModel):
    origin: str
    destination: str
    load_type: str = "STANDARD"
    origin_lat: Optional[float] = None
    origin_lng: Optional[float] = None
    dest_lat: Optional[float] = None
    dest_lng: Optional[float] = None


class ShipmentCreate(BaseModel):
    origin: str
    destination: str
    load_type: str = "STANDARD"
    tracking_id: Optional[str] = None
    tracking_number: Optional[str] = None
    origin_lat: Optional[float] = None
    origin_lng: Optional[float] = None
    dest_lat: Optional[float] = None
    dest_lng: Optional[float] = None
    carrier_id: Optional[int] = None
    driver_id: Optional[int] = None


class ShipmentStartRequest(BaseModel):
    tick_seconds: int = Field(default=5, ge=3, le=5)


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


class TrackingLogResponse(BaseModel):
    latitude: float
    longitude: float
    timestamp: str


class RoutePlanResponse(BaseModel):
    origin: str
    destination: str
    load_type: str
    origin_lat: float
    origin_lng: float
    dest_lat: float
    dest_lng: float
    route_coordinates: List[List[float]]
    distance_km: float
    eta_hours: float
    fuel_liters: float
    average_speed_kmh: float
    fuel_consumption_rate: float
