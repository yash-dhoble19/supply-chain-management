"""
Logistics routes — /logistics/*
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import models
import database
from schemas.logistics import RouteRequest, CarrierCreate, DriverCreate, ShipmentCreate, ShipmentUpdate
from services import logistics_service
from services.background_tasks import generate_and_store_insight

router = APIRouter(prefix="/logistics", tags=["Logistics"])


@router.post("/plan_route")
def plan_route(request: RouteRequest, background_tasks: BackgroundTasks, db: Session = Depends(database.get_db)):
    start_lat, start_lon = logistics_service.get_coordinates(request.start_address)
    end_lat, end_lon = logistics_service.get_coordinates(request.end_address)

    if not (start_lat and start_lon):
        raise HTTPException(400, "Invalid Start Address")
    if not (end_lat and end_lon):
        raise HTTPException(400, "Invalid End Address")

    waypoint_coords = []
    waypoint_names = []
    if request.waypoints:
        for wp in request.waypoints:
            if wp.strip():
                lat, lon = logistics_service.get_coordinates(wp)
                if lat and lon:
                    waypoint_coords.append((lat, lon))
                    waypoint_names.append(wp)

    route_data = logistics_service.get_route_data(
        (start_lat, start_lon), (end_lat, end_lon), waypoint_coords
    )
    if not route_data:
        raise HTTPException(500, "Could not calc route")

    route_desc = f"from {request.start_address} to {request.end_address}"
    if waypoint_names:
        route_desc += f" via {', '.join(waypoint_names)}"

    duration_hrs = float(route_data.get("duration_min", 0)) / 60.0
    dist_km = float(route_data.get("distance_km", 0))
    if duration_hrs > 8 or dist_km > 600:
        risk_analysis = "HIGH_RISK: Long transit duration requiring layovers. Monitor tracking closely."
    elif duration_hrs > 4 or dist_km > 300:
        risk_analysis = "MEDIUM_RISK: Inter-city regional transit."
    else:
        risk_analysis = "LOW_RISK: Short distance transit."

    # Background task to run full AI evaluation and cache to db
    background_tasks.add_task(
        generate_and_store_insight,
        db=db,
        entity_type="ROUTE",
        entity_id=route_desc,
        insight_type="ROUTE_RISK",
        route_desc=route_desc,
        distance_km=route_data.get("distance_km"),
        duration_min=route_data.get("duration_min")
    )

    return {
        "start_coords": [start_lat, start_lon],
        "end_coords": [end_lat, end_lon],
        "waypoints": waypoint_coords,
        "route_info": route_data,
        "risk_analysis": risk_analysis,
    }


# ── Carriers ─────────────────────────────────────────────────────────


@router.post("/carriers/create")
def create_carrier(carrier: CarrierCreate, db: Session = Depends(database.get_db)):
    db_carrier = models.Carrier(**carrier.dict())
    try:
        db.add(db_carrier)
        db.commit()
        db.refresh(db_carrier)
        return db_carrier
    except Exception as e:
        db.rollback()
        raise HTTPException(400, f"Error creating carrier: {e}")


@router.get("/carriers/list")
def list_carriers(db: Session = Depends(database.get_db)):
    return db.query(models.Carrier).all()


# ── Drivers ──────────────────────────────────────────────────────────


@router.post("/drivers/create")
def create_driver(driver: DriverCreate, db: Session = Depends(database.get_db)):
    db_driver = models.Driver(**driver.dict())
    try:
        db.add(db_driver)
        db.commit()
        db.refresh(db_driver)
        return db_driver
    except Exception as e:
        db.rollback()
        raise HTTPException(400, f"Error creating driver: {e}")


@router.get("/drivers/list")
def list_drivers(carrier_id: Optional[int] = None, db: Session = Depends(database.get_db)):
    q = db.query(models.Driver)
    if carrier_id:
        q = q.filter(models.Driver.carrier_id == carrier_id)
    return q.all()


# ── Shipments ────────────────────────────────────────────────────────


@router.post("/shipments/create")
def create_shipment(shipment: ShipmentCreate, db: Session = Depends(database.get_db)):
    db_shipment, error = logistics_service.create_shipment(
        db, shipment.tracking_number, shipment.origin, shipment.destination,
        shipment.carrier_id, shipment.driver_id, shipment.waypoints, shipment.scheduled_date,
    )
    if error:
        raise HTTPException(400, error)
    return db_shipment


@router.get("/shipments/list")
def list_shipments(db: Session = Depends(database.get_db)):
    return db.query(models.Shipment).all()


@router.post("/shipments/{id}/update")
def update_shipment(id: int, update: ShipmentUpdate, db: Session = Depends(database.get_db)):
    shipment = db.query(models.Shipment).filter(models.Shipment.id == id).first()
    if not shipment:
        raise HTTPException(404, "Shipment not found")
    return logistics_service.update_shipment(
        db, shipment, update.status,
        update.current_location_lat, update.current_location_lon, update.progress_percent,
    )
