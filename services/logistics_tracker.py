import asyncio
import math
from datetime import datetime

from fastapi import WebSocket
from sqlalchemy.orm import Session

import models
from database import SessionLocal
from services import logistics_service


class LogisticsRealtimeManager:
    def __init__(self) -> None:
        self._shipment_tasks: dict[int, asyncio.Task] = {}
        self._connections: dict[int, set[WebSocket]] = {}

    async def connect(self, shipment_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(shipment_id, set()).add(websocket)

    def disconnect(self, shipment_id: int, websocket: WebSocket) -> None:
        connections = self._connections.get(shipment_id)
        if not connections:
            return
        connections.discard(websocket)
        if not connections:
            self._connections.pop(shipment_id, None)

    async def broadcast(self, shipment_id: int, payload: dict) -> None:
        stale_connections: list[WebSocket] = []
        for websocket in list(self._connections.get(shipment_id, set())):
            try:
                await websocket.send_json(payload)
            except Exception:
                stale_connections.append(websocket)

        for websocket in stale_connections:
            self.disconnect(shipment_id, websocket)

    def ensure_tracking(self, shipment_id: int, tick_seconds: int = 5) -> None:
        existing_task = self._shipment_tasks.get(shipment_id)
        if existing_task and not existing_task.done():
            return

        self._shipment_tasks[shipment_id] = asyncio.create_task(
            self._run_shipment_tracking(shipment_id, tick_seconds)
        )

    async def resume_in_transit_shipments(self) -> None:
        db = SessionLocal()
        try:
            shipments = (
                db.query(models.Shipment)
                .filter(models.Shipment.status == "IN_TRANSIT")
                .all()
            )
            for shipment in shipments:
                self.ensure_tracking(shipment.id)
        finally:
            db.close()

    async def _run_shipment_tracking(self, shipment_id: int, tick_seconds: int) -> None:
        try:
            while True:
                payload = await self._advance_shipment(shipment_id, tick_seconds)
                if payload is None:
                    return

                await self.broadcast(shipment_id, payload)

                if payload["type"] == "shipment.delivered":
                    return

                await asyncio.sleep(tick_seconds)
        finally:
            self._shipment_tasks.pop(shipment_id, None)

    async def _advance_shipment(self, shipment_id: int, tick_seconds: int) -> dict | None:
        db = SessionLocal()
        try:
            shipment = db.query(models.Shipment).filter(models.Shipment.id == shipment_id).first()
            if shipment is None or shipment.status != "IN_TRANSIT":
                return None

            route_coordinates = logistics_service.ensure_route_geometry(shipment, db)
            if len(route_coordinates) < 2:
                shipment.status = "DELIVERED"
                shipment.progress = 100.0
                shipment.progress_percent = 100.0
                shipment.current_lat = shipment.destination_lat
                shipment.current_lng = shipment.destination_lng
                shipment.current_location_lat = shipment.destination_lat
                shipment.current_location_lon = shipment.destination_lng
                shipment.delivered_at = datetime.utcnow()
                shipment.eta = shipment.delivered_at
                logistics_service.append_tracking_log(
                    db,
                    shipment.id,
                    shipment.destination_lat,
                    shipment.destination_lng,
                    shipment.delivered_at,
                )
                db.commit()
                db.refresh(shipment)
                return self._shipment_payload(shipment, "shipment.delivered", db)

            cumulative_distances = build_cumulative_distances(route_coordinates)
            total_distance = cumulative_distances[-1] if cumulative_distances else shipment.distance_km
            distance_per_tick = (shipment.average_speed_kmh or 50.0) * (tick_seconds / 3600.0)

            if shipment.progress is not None:
                current_distance = total_distance * (shipment.progress / 100.0)
            else:
                current_distance = infer_distance_from_location(
                    route_coordinates,
                    cumulative_distances,
                    shipment.current_lat or shipment.current_location_lat,
                    shipment.current_lng or shipment.current_location_lon,
                )

            next_distance = min(total_distance, current_distance + distance_per_tick)
            next_lat, next_lng = interpolate_position(route_coordinates, cumulative_distances, next_distance)
            progress = 100.0 if total_distance <= 0 else min(100.0, (next_distance / total_distance) * 100.0)
            remaining_distance = max(0.0, total_distance - next_distance)

            shipment.current_lat = next_lat
            shipment.current_lng = next_lng
            shipment.current_location_lat = next_lat
            shipment.current_location_lon = next_lng
            shipment.progress = round(progress, 2)
            shipment.progress_percent = round(progress, 2)
            shipment.eta = logistics_service.calculate_eta(
                remaining_distance,
                shipment.average_speed_kmh or 50.0,
            )

            status = "shipment.updated"
            if progress >= 100.0 or remaining_distance <= 0.05:
                shipment.status = "DELIVERED"
                shipment.progress = 100.0
                shipment.progress_percent = 100.0
                shipment.current_lat = shipment.destination_lat
                shipment.current_lng = shipment.destination_lng
                shipment.current_location_lat = shipment.destination_lat
                shipment.current_location_lon = shipment.destination_lng
                shipment.delivered_at = datetime.utcnow()
                shipment.eta = shipment.delivered_at
                status = "shipment.delivered"

            logistics_service.append_tracking_log(
                db,
                shipment.id,
                shipment.current_lat,
                shipment.current_lng,
                datetime.utcnow(),
            )

            db.commit()
            db.refresh(shipment)
            return self._shipment_payload(shipment, status, db)
        finally:
            db.close()

    def _shipment_payload(self, shipment: models.Shipment, event_type: str, db: Session) -> dict:
        tracking_logs = (
            db.query(models.TrackingLog)
            .filter(models.TrackingLog.shipment_id == shipment.id)
            .order_by(models.TrackingLog.timestamp.asc())
            .all()
        )
        return {
            "type": event_type,
            "shipment": logistics_service.serialize_shipment(shipment),
            "tracking": [logistics_service.serialize_tracking_log(log) for log in tracking_logs[-50:]],
        }


def build_cumulative_distances(route_coordinates: list[list[float]]) -> list[float]:
    if not route_coordinates:
        return [0.0]

    cumulative = [0.0]
    running_total = 0.0
    for index in range(1, len(route_coordinates)):
        previous = route_coordinates[index - 1]
        current = route_coordinates[index]
        running_total += logistics_service.haversine_km(
            previous[0],
            previous[1],
            current[0],
            current[1],
        )
        cumulative.append(running_total)
    return cumulative


def interpolate_position(
    route_coordinates: list[list[float]],
    cumulative_distances: list[float],
    target_distance: float,
) -> tuple[float, float]:
    if len(route_coordinates) == 1:
        return route_coordinates[0][0], route_coordinates[0][1]

    if target_distance <= 0:
        return route_coordinates[0][0], route_coordinates[0][1]

    total_distance = cumulative_distances[-1]
    if target_distance >= total_distance:
        return route_coordinates[-1][0], route_coordinates[-1][1]

    for index in range(1, len(cumulative_distances)):
        if cumulative_distances[index] >= target_distance:
            segment_start_distance = cumulative_distances[index - 1]
            segment_end_distance = cumulative_distances[index]
            segment_length = max(segment_end_distance - segment_start_distance, 1e-6)
            ratio = (target_distance - segment_start_distance) / segment_length

            start_lat, start_lng = route_coordinates[index - 1]
            end_lat, end_lng = route_coordinates[index]

            latitude = start_lat + (end_lat - start_lat) * ratio
            longitude = start_lng + (end_lng - start_lng) * ratio
            return latitude, longitude

    return route_coordinates[-1][0], route_coordinates[-1][1]


def infer_distance_from_location(
    route_coordinates: list[list[float]],
    cumulative_distances: list[float],
    current_lat: float | None,
    current_lng: float | None,
) -> float:
    if current_lat is None or current_lng is None:
        return 0.0

    best_index = 0
    best_distance = math.inf
    for index, coordinate in enumerate(route_coordinates):
        candidate_distance = logistics_service.haversine_km(
            current_lat,
            current_lng,
            coordinate[0],
            coordinate[1],
        )
        if candidate_distance < best_distance:
            best_distance = candidate_distance
            best_index = index

    return cumulative_distances[min(best_index, len(cumulative_distances) - 1)]


realtime_manager = LogisticsRealtimeManager()
