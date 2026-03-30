"""
Logistics service — geocoding, routing, shipment management.
"""
import json
from datetime import datetime, timedelta
from typing import Optional

import requests
from geopy.geocoders import Nominatim
from sqlalchemy.orm import Session

import models

_geolocator = Nominatim(user_agent="scm_app_free_v1")


def get_coordinates(address: str):
    try:
        location = _geolocator.geocode(address)
        if location:
            return location.latitude, location.longitude
        return None, None
    except Exception:
        return None, None


def get_route_data(start_coords, end_coords, waypoint_coords=None) -> Optional[dict]:
    coords = [start_coords]
    if waypoint_coords:
        coords.extend(waypoint_coords)
    coords.append(end_coords)

    coord_str = ";".join([f"{c[1]},{c[0]}" for c in coords])
    url = f"http://router.project-osrm.org/route/v1/driving/{coord_str}?overview=full"

    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if data["code"] == "Ok":
            route = data["routes"][0]
            distance_km = route["distance"] / 1000
            return {
                "distance_km": round(distance_km, 2),
                "duration_min": round(route["duration"] / 60, 0),
                "geometry": route["geometry"],
                "estimated_cost": round(distance_km * 1.5, 2),
            }
        return None
    except Exception:
        return None


def create_shipment(db: Session, tracking_number: str, origin: str, destination: str,
                    carrier_id: Optional[int], driver_id: Optional[int],
                    waypoints: list[str], scheduled_date: Optional[str]):
    start_lat, start_lon = get_coordinates(origin)
    end_lat, end_lon = get_coordinates(destination)

    if not (start_lat and start_lon and end_lat and end_lon):
        return None, "Invalid addresses"

    waypoint_coords = []
    if waypoints:
        for wp in waypoints:
            lat, lon = get_coordinates(wp)
            if lat:
                waypoint_coords.append((lat, lon))

    route_data = get_route_data((start_lat, start_lon), (end_lat, end_lon), waypoint_coords)

    db_shipment = models.Shipment(
        tracking_number=tracking_number, origin=origin, destination=destination,
        waypoints=json.dumps(waypoints), carrier_id=carrier_id, driver_id=driver_id,
        status="SCHEDULED", origin_lat=start_lat, origin_lon=start_lon,
        origin_snapped=False, current_location_lat=start_lat,
        current_location_lon=start_lon, progress_percent=0.0,
    )

    if route_data:
        db_shipment.route_geometry = route_data["geometry"]
        db_shipment.total_distance_km = route_data["distance_km"]
        hours = route_data["duration_min"] / 60
        db_shipment.eta = datetime.now() + timedelta(hours=hours)

    if scheduled_date:
        try:
            db_shipment.scheduled_date = datetime.fromisoformat(scheduled_date)
        except Exception:
            pass

    db.add(db_shipment)
    db.commit()
    db.refresh(db_shipment)
    return db_shipment, None


def update_shipment(db: Session, shipment, status=None,
                    current_location_lat=None, current_location_lon=None,
                    progress_percent=None):
    if current_location_lat and current_location_lon:
        try:
            from geopy.distance import geodesic

            if not shipment.origin_snapped:
                shipment.origin_lat = current_location_lat
                shipment.origin_lon = current_location_lon
                shipment.origin_snapped = True
                dest_lat, dest_lon = get_coordinates(shipment.destination)
                if dest_lat:
                    shipment.total_distance_km = geodesic(
                        (shipment.origin_lat, shipment.origin_lon), (dest_lat, dest_lon)
                    ).kilometers
                shipment.progress_percent = 0.0
            else:
                origin_point = (shipment.origin_lat, shipment.origin_lon)
                current_point = (current_location_lat, current_location_lon)
                dest_lat, dest_lon = get_coordinates(shipment.destination)
                if dest_lat and shipment.total_distance_km > 0:
                    distance_traveled = geodesic(origin_point, current_point).kilometers
                    progress = min(100.0, (distance_traveled / shipment.total_distance_km) * 100)
                    shipment.progress_percent = round(progress, 2)
        except Exception as e:
            print(f"Progress calculation error: {e}")

    if status:
        shipment.status = status
    if current_location_lat:
        shipment.current_location_lat = current_location_lat
    if current_location_lon:
        shipment.current_location_lon = current_location_lon
    if progress_percent is not None:
        shipment.progress_percent = progress_percent

    db.commit()
    return shipment
