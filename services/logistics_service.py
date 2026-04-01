from concurrent.futures import ThreadPoolExecutor
import json
import math
from datetime import datetime, timedelta
from threading import Lock
from time import time
from typing import Optional
from uuid import uuid4

import requests
from sqlalchemy.orm import Session

import models


OSRM_ROUTE_URL = "https://router.project-osrm.org/route/v1/driving"
NOMINATIM_SEARCH_URL = "https://nominatim.openstreetmap.org/search"
DEFAULT_TICK_SECONDS = 5
GEOCODE_CACHE_TTL_SECONDS = 60 * 60
ROUTE_CACHE_TTL_SECONDS = 10 * 60
GEOCODE_TIMEOUT_SECONDS = 4
ROUTE_TIMEOUT_SECONDS = 5

LOAD_TYPE_PROFILES = {
    "STANDARD": {"average_speed_kmh": 50.0, "fuel_consumption_rate": 0.28},
    "BULK": {"average_speed_kmh": 42.0, "fuel_consumption_rate": 0.4},
    "PERISHABLE": {"average_speed_kmh": 46.0, "fuel_consumption_rate": 0.33},
    "FRAGILE": {"average_speed_kmh": 44.0, "fuel_consumption_rate": 0.31},
    "EXPRESS": {"average_speed_kmh": 58.0, "fuel_consumption_rate": 0.29},
}

_http_session = requests.Session()
_http_session.headers.update({"User-Agent": "chainmind-logistics"})
_cache_lock = Lock()
_geocode_cache: dict[str, tuple[float, float, float]] = {}
_route_cache: dict[str, tuple[dict, float]] = {}


def normalize_load_type(load_type: Optional[str]) -> str:
    candidate = (load_type or "STANDARD").strip().upper()
    return candidate if candidate in LOAD_TYPE_PROFILES else "STANDARD"


def get_load_profile(load_type: Optional[str]) -> dict:
    return LOAD_TYPE_PROFILES[normalize_load_type(load_type)]


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius_km = 6371.0
    lat1_rad, lng1_rad = math.radians(lat1), math.radians(lng1)
    lat2_rad, lng2_rad = math.radians(lat2), math.radians(lng2)
    dlat = lat2_rad - lat1_rad
    dlng = lng2_rad - lng1_rad
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius_km * c


def distance_for_route_coordinates(route_coordinates: list[list[float]]) -> float:
    if len(route_coordinates) < 2:
        return 0.0

    total_distance = 0.0
    for index in range(1, len(route_coordinates)):
        previous = route_coordinates[index - 1]
        current = route_coordinates[index]
        total_distance += haversine_km(previous[0], previous[1], current[0], current[1])
    return total_distance


def _get_cached_value(cache: dict, key: str, ttl_seconds: int):
    with _cache_lock:
        cached = cache.get(key)
        if not cached:
            return None

        value, cached_at = cached
        if time() - cached_at > ttl_seconds:
            cache.pop(key, None)
            return None

        return value


def _set_cached_value(cache: dict, key: str, value) -> None:
    with _cache_lock:
        cache[key] = (value, time())


def get_coordinates(address: str) -> tuple[Optional[float], Optional[float]]:
    normalized_address = " ".join(address.strip().lower().split())
    cached_coordinates = _get_cached_value(_geocode_cache, normalized_address, GEOCODE_CACHE_TTL_SECONDS)
    if cached_coordinates:
        return cached_coordinates

    try:
        response = _http_session.get(
            NOMINATIM_SEARCH_URL,
            params={
                "q": address,
                "format": "jsonv2",
                "limit": 1,
                "addressdetails": 0,
            },
            timeout=GEOCODE_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
        if not payload:
            return None, None

        coordinates = (float(payload[0]["lat"]), float(payload[0]["lon"]))
        _set_cached_value(_geocode_cache, normalized_address, coordinates)
        return coordinates
    except Exception:
        return None, None


def _resolve_single_coordinates(
    address: str,
    provided_lat: Optional[float] = None,
    provided_lng: Optional[float] = None,
) -> tuple[float, float]:
    if provided_lat is not None and provided_lng is not None:
        return float(provided_lat), float(provided_lng)

    latitude, longitude = get_coordinates(address)
    if latitude is None or longitude is None:
        raise ValueError(f"Could not resolve coordinates for '{address}'")

    return latitude, longitude


def resolve_coordinates(
    address: str,
    provided_lat: Optional[float] = None,
    provided_lng: Optional[float] = None,
) -> tuple[float, float]:
    return _resolve_single_coordinates(address, provided_lat, provided_lng)


def resolve_route_coordinates(
    origin: str,
    destination: str,
    origin_lat: Optional[float] = None,
    origin_lng: Optional[float] = None,
    dest_lat: Optional[float] = None,
    dest_lng: Optional[float] = None,
) -> tuple[tuple[float, float], tuple[float, float]]:
    with ThreadPoolExecutor(max_workers=2) as executor:
        origin_future = executor.submit(_resolve_single_coordinates, origin, origin_lat, origin_lng)
        destination_future = executor.submit(_resolve_single_coordinates, destination, dest_lat, dest_lng)
        return origin_future.result(), destination_future.result()


def get_route_data(
    origin: tuple[float, float],
    destination: tuple[float, float],
) -> dict:
    route_cache_key = (
        f"{origin[0]:.5f},{origin[1]:.5f}:{destination[0]:.5f},{destination[1]:.5f}"
    )
    cached_route = _get_cached_value(_route_cache, route_cache_key, ROUTE_CACHE_TTL_SECONDS)
    if cached_route:
        return cached_route

    coord_string = f"{origin[1]},{origin[0]};{destination[1]},{destination[0]}"
    response = _http_session.get(
        f"{OSRM_ROUTE_URL}/{coord_string}",
        params={"overview": "simplified", "geometries": "geojson", "steps": "false"},
        timeout=ROUTE_TIMEOUT_SECONDS,
    )
    response.raise_for_status()

    data = response.json()
    if data.get("code") != "Ok" or not data.get("routes"):
        raise ValueError("Routing provider could not build a route for the supplied coordinates")

    route = data["routes"][0]
    coordinates = [
        [float(latitude), float(longitude)]
        for longitude, latitude in route["geometry"]["coordinates"]
    ]

    distance_km = round(route["distance"] / 1000, 2)
    duration_seconds = float(route["duration"])
    route_data = {
        "route_coordinates": coordinates,
        "distance_km": distance_km,
        "duration_seconds": duration_seconds,
    }
    _set_cached_value(_route_cache, route_cache_key, route_data)
    return route_data


def build_fallback_route_data(
    origin: tuple[float, float],
    destination: tuple[float, float],
    average_speed_kmh: float,
) -> dict:
    distance_km = round(haversine_km(origin[0], origin[1], destination[0], destination[1]), 2)
    duration_seconds = (distance_km / average_speed_kmh) * 3600 if average_speed_kmh > 0 else 0.0
    return {
        "route_coordinates": [
            [float(origin[0]), float(origin[1])],
            [float(destination[0]), float(destination[1])],
        ],
        "distance_km": distance_km,
        "duration_seconds": duration_seconds,
    }


def calculate_eta(distance_km: float, average_speed_kmh: float, started_at: Optional[datetime] = None) -> datetime:
    base_time = started_at or datetime.utcnow()
    hours = distance_km / average_speed_kmh if average_speed_kmh > 0 else 0
    return base_time + timedelta(hours=hours)


def calculate_fuel(distance_km: float, fuel_consumption_rate: float) -> float:
    return round(distance_km * fuel_consumption_rate, 2)


def generate_tracking_reference(prefix: str = "TRK") -> str:
    token = uuid4().hex[:8].upper()
    return f"{prefix}-{token}"


def build_route_plan(
    origin: str,
    destination: str,
    load_type: str,
    origin_lat: Optional[float] = None,
    origin_lng: Optional[float] = None,
    dest_lat: Optional[float] = None,
    dest_lng: Optional[float] = None,
) -> dict:
    normalized_load_type = normalize_load_type(load_type)
    profile = get_load_profile(normalized_load_type)
    resolved_origin, resolved_destination = resolve_route_coordinates(
        origin,
        destination,
        origin_lat,
        origin_lng,
        dest_lat,
        dest_lng,
    )
    try:
        route_data = get_route_data(resolved_origin, resolved_destination)
    except Exception:
        route_data = build_fallback_route_data(
            resolved_origin,
            resolved_destination,
            profile["average_speed_kmh"],
        )

    distance_km = route_data["distance_km"] or round(
        distance_for_route_coordinates(route_data["route_coordinates"]), 2
    )
    eta_hours = round(distance_km / profile["average_speed_kmh"], 2)
    fuel_liters = calculate_fuel(distance_km, profile["fuel_consumption_rate"])

    return {
        "origin": origin,
        "destination": destination,
        "load_type": normalized_load_type,
        "origin_lat": resolved_origin[0],
        "origin_lng": resolved_origin[1],
        "dest_lat": resolved_destination[0],
        "dest_lng": resolved_destination[1],
        "route_coordinates": route_data["route_coordinates"],
        "distance_km": distance_km,
        "duration_seconds": route_data["duration_seconds"],
        "eta_hours": eta_hours,
        "fuel_liters": fuel_liters,
        "average_speed_kmh": profile["average_speed_kmh"],
        "fuel_consumption_rate": profile["fuel_consumption_rate"],
    }


def parse_route_geometry(route_geometry: Optional[str]) -> list[list[float]]:
    if not route_geometry:
        return []

    try:
        decoded = json.loads(route_geometry)
        if isinstance(decoded, list):
            return [[float(pair[0]), float(pair[1])] for pair in decoded]
    except Exception:
        return []

    return []


def ensure_route_geometry(shipment: models.Shipment, db: Session) -> list[list[float]]:
    coordinates = parse_route_geometry(shipment.route_geometry)
    if coordinates:
        return coordinates

    route_plan = build_route_plan(
        origin=shipment.origin,
        destination=shipment.destination,
        load_type=shipment.load_type,
        origin_lat=shipment.origin_lat,
        origin_lng=shipment.origin_lng or shipment.origin_lon,
        dest_lat=shipment.destination_lat,
        dest_lng=shipment.destination_lng,
    )

    apply_route_plan_to_shipment(shipment, route_plan)
    db.commit()
    db.refresh(shipment)
    return route_plan["route_coordinates"]


def apply_route_plan_to_shipment(shipment: models.Shipment, route_plan: dict) -> None:
    shipment.origin_lat = route_plan["origin_lat"]
    shipment.origin_lon = route_plan["origin_lng"]
    shipment.origin_lng = route_plan["origin_lng"]
    shipment.destination_lat = route_plan["dest_lat"]
    shipment.destination_lng = route_plan["dest_lng"]
    shipment.current_location_lat = shipment.current_location_lat or route_plan["origin_lat"]
    shipment.current_location_lon = shipment.current_location_lon or route_plan["origin_lng"]
    shipment.current_lat = shipment.current_lat or route_plan["origin_lat"]
    shipment.current_lng = shipment.current_lng or route_plan["origin_lng"]
    shipment.total_distance_km = route_plan["distance_km"]
    shipment.distance_km = route_plan["distance_km"]
    shipment.route_duration_seconds = route_plan["duration_seconds"]
    shipment.route_geometry = json.dumps(route_plan["route_coordinates"])
    shipment.average_speed_kmh = route_plan["average_speed_kmh"]
    shipment.fuel_consumption_rate = route_plan["fuel_consumption_rate"]
    shipment.fuel_required_liters = route_plan["fuel_liters"]
    shipment.load_type = route_plan["load_type"]
    shipment.progress_percent = shipment.progress_percent or 0.0
    shipment.progress = shipment.progress or shipment.progress_percent or 0.0
    shipment.eta = calculate_eta(route_plan["distance_km"], route_plan["average_speed_kmh"])


def create_shipment(
    db: Session,
    *,
    origin: str,
    destination: str,
    load_type: str,
    tracking_id: Optional[str] = None,
    tracking_number: Optional[str] = None,
    origin_lat: Optional[float] = None,
    origin_lng: Optional[float] = None,
    dest_lat: Optional[float] = None,
    dest_lng: Optional[float] = None,
    carrier_id: Optional[int] = None,
    driver_id: Optional[int] = None,
) -> models.Shipment:
    route_plan = build_route_plan(
        origin=origin,
        destination=destination,
        load_type=load_type,
        origin_lat=origin_lat,
        origin_lng=origin_lng,
        dest_lat=dest_lat,
        dest_lng=dest_lng,
    )

    final_tracking_id = tracking_id or tracking_number or generate_tracking_reference("SHP")
    final_tracking_number = tracking_number or final_tracking_id

    if db.query(models.Shipment).filter(models.Shipment.tracking_number == final_tracking_number).first():
        final_tracking_number = generate_tracking_reference("SHP")
    if db.query(models.Shipment).filter(models.Shipment.tracking_id == final_tracking_id).first():
        final_tracking_id = generate_tracking_reference("SHP")

    shipment = models.Shipment(
        tracking_number=final_tracking_number,
        tracking_id=final_tracking_id,
        origin=origin,
        destination=destination,
        status="CREATED",
        carrier_id=carrier_id,
        driver_id=driver_id,
    )
    apply_route_plan_to_shipment(shipment, route_plan)

    db.add(shipment)
    db.commit()
    db.refresh(shipment)
    return shipment


def get_remaining_distance_km(shipment: models.Shipment) -> float:
    if shipment.distance_km and shipment.progress is not None:
        return max(0.0, shipment.distance_km * (1 - (shipment.progress / 100.0)))

    if (
        shipment.current_lat is not None
        and shipment.current_lng is not None
        and shipment.destination_lat is not None
        and shipment.destination_lng is not None
    ):
        return haversine_km(
            shipment.current_lat,
            shipment.current_lng,
            shipment.destination_lat,
            shipment.destination_lng,
        )

    return 0.0


def append_tracking_log(
    db: Session,
    shipment_id: int,
    latitude: float,
    longitude: float,
    timestamp: Optional[datetime] = None,
) -> models.TrackingLog:
    tracking_log = models.TrackingLog(
        shipment_id=shipment_id,
        latitude=latitude,
        longitude=longitude,
        timestamp=timestamp or datetime.utcnow(),
    )
    db.add(tracking_log)
    return tracking_log


def start_shipment(db: Session, shipment: models.Shipment) -> models.Shipment:
    if shipment.status == "DELIVERED":
        raise ValueError("Delivered shipments cannot be restarted")

    ensure_route_geometry(shipment, db)

    if shipment.started_at is None:
        shipment.started_at = datetime.utcnow()

    shipment.status = "IN_TRANSIT"
    shipment.delivered_at = None
    shipment.progress_percent = shipment.progress or shipment.progress_percent or 0.0
    shipment.progress = shipment.progress_percent

    remaining_distance_km = get_remaining_distance_km(shipment) or shipment.distance_km
    shipment.eta = calculate_eta(remaining_distance_km, shipment.average_speed_kmh or 50.0)

    current_lat = shipment.current_lat or shipment.current_location_lat or shipment.origin_lat
    current_lng = shipment.current_lng or shipment.current_location_lon or shipment.origin_lng or shipment.origin_lon
    shipment.current_location_lat = current_lat
    shipment.current_location_lon = current_lng
    shipment.current_lat = current_lat
    shipment.current_lng = current_lng

    if shipment.tracking_logs:
        latest_log = shipment.tracking_logs[-1]
        if latest_log.latitude != current_lat or latest_log.longitude != current_lng:
            append_tracking_log(db, shipment.id, current_lat, current_lng)
    else:
        append_tracking_log(db, shipment.id, current_lat, current_lng)

    db.commit()
    db.refresh(shipment)
    return shipment


def serialize_tracking_log(tracking_log: models.TrackingLog) -> dict:
    timestamp = tracking_log.timestamp or datetime.utcnow()
    return {
        "id": tracking_log.id,
        "latitude": round(float(tracking_log.latitude), 6),
        "longitude": round(float(tracking_log.longitude), 6),
        "timestamp": timestamp.isoformat(),
    }


def serialize_shipment(shipment: models.Shipment, include_route_coordinates: bool = True) -> dict:
    route_coordinates = parse_route_geometry(shipment.route_geometry) if include_route_coordinates else []
    eta = shipment.eta.isoformat() if shipment.eta else None
    started_at = shipment.started_at.isoformat() if shipment.started_at else None
    delivered_at = shipment.delivered_at.isoformat() if shipment.delivered_at else None

    return {
        "id": shipment.id,
        "trackingId": shipment.tracking_id or shipment.tracking_number,
        "trackingNumber": shipment.tracking_number,
        "origin": shipment.origin,
        "destination": shipment.destination,
        "originLat": shipment.origin_lat,
        "originLng": shipment.origin_lng or shipment.origin_lon,
        "destLat": shipment.destination_lat,
        "destLng": shipment.destination_lng,
        "currentLat": shipment.current_lat or shipment.current_location_lat,
        "currentLng": shipment.current_lng or shipment.current_location_lon,
        "status": shipment.status,
        "progress": round(float(shipment.progress or shipment.progress_percent or 0.0), 2),
        "distanceKm": round(float(shipment.distance_km or shipment.total_distance_km or 0.0), 2),
        "eta": eta,
        "startedAt": started_at,
        "deliveredAt": delivered_at,
        "loadType": shipment.load_type,
        "averageSpeedKmh": round(float(shipment.average_speed_kmh or 0.0), 2),
        "fuelConsumptionRate": round(float(shipment.fuel_consumption_rate or 0.0), 3),
        "fuelLiters": round(float(shipment.fuel_required_liters or 0.0), 2),
        "routeCoordinates": route_coordinates,
        "routeDurationSeconds": round(float(shipment.route_duration_seconds or 0.0), 2),
        "carrierId": shipment.carrier_id,
        "driverId": shipment.driver_id,
        "createdAt": shipment.created_at.isoformat() if shipment.created_at else None,
    }


def serialize_route_plan(route_plan: dict) -> dict:
    return {
        "origin": route_plan["origin"],
        "destination": route_plan["destination"],
        "load_type": route_plan["load_type"],
        "origin_lat": route_plan["origin_lat"],
        "origin_lng": route_plan["origin_lng"],
        "dest_lat": route_plan["dest_lat"],
        "dest_lng": route_plan["dest_lng"],
        "route_coordinates": route_plan["route_coordinates"],
        "distance_km": round(float(route_plan["distance_km"]), 2),
        "eta_hours": round(float(route_plan["eta_hours"]), 2),
        "fuel_liters": round(float(route_plan["fuel_liters"]), 2),
        "average_speed_kmh": round(float(route_plan["average_speed_kmh"]), 2),
        "fuel_consumption_rate": round(float(route_plan["fuel_consumption_rate"]), 3),
    }
