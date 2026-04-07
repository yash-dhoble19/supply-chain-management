from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session, load_only

import database
import models
from schemas.logistics import (
    CarrierCreate,
    DriverCreate,
    RoutePlanRequest,
    ShipmentCreate,
    ShipmentStartRequest,
)
from services import logistics_service
from services.logistics_tracker import realtime_manager


router = APIRouter(prefix="/api", tags=["Logistics"])


SHIPMENT_LIST_FIELDS = (
    models.Shipment.id,
    models.Shipment.tracking_number,
    models.Shipment.tracking_id,
    models.Shipment.origin,
    models.Shipment.destination,
    models.Shipment.origin_lat,
    models.Shipment.origin_lon,
    models.Shipment.origin_lng,
    models.Shipment.destination_lat,
    models.Shipment.destination_lng,
    models.Shipment.current_location_lat,
    models.Shipment.current_location_lon,
    models.Shipment.current_lat,
    models.Shipment.current_lng,
    models.Shipment.status,
    models.Shipment.progress_percent,
    models.Shipment.progress,
    models.Shipment.distance_km,
    models.Shipment.eta,
    models.Shipment.started_at,
    models.Shipment.delivered_at,
    models.Shipment.load_type,
    models.Shipment.average_speed_kmh,
    models.Shipment.fuel_consumption_rate,
    models.Shipment.fuel_required_liters,
    models.Shipment.route_duration_seconds,
    models.Shipment.carrier_id,
    models.Shipment.driver_id,
    models.Shipment.created_at,
)


def _get_recent_tracking_logs(db: Session, shipment_id: int, limit: int = 50):
    rows = (
        db.query(models.TrackingLog)
        .filter(models.TrackingLog.shipment_id == shipment_id)
        .order_by(models.TrackingLog.timestamp.desc())
        .limit(limit)
        .all()
    )
    return list(reversed(rows))


@router.post("/routes/plan")
def plan_route(request: RoutePlanRequest):
    try:
        route_plan = logistics_service.build_route_plan(
            origin=request.origin,
            destination=request.destination,
            load_type=request.load_type,
            origin_lat=request.origin_lat,
            origin_lng=request.origin_lng,
            dest_lat=request.dest_lat,
            dest_lng=request.dest_lng,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Route planning failed: {error}") from error

    return logistics_service.serialize_route_plan(route_plan)


@router.post("/shipments/create")
def create_shipment(request: ShipmentCreate, db: Session = Depends(database.get_db)):
    try:
        shipment = logistics_service.create_shipment(
            db,
            origin=request.origin,
            destination=request.destination,
            load_type=request.load_type,
            tracking_id=request.tracking_id,
            tracking_number=request.tracking_number,
            origin_lat=request.origin_lat,
            origin_lng=request.origin_lng,
            dest_lat=request.dest_lat,
            dest_lng=request.dest_lng,
            carrier_id=request.carrier_id,
            driver_id=request.driver_id,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Shipment creation failed: {error}") from error

    return logistics_service.serialize_shipment(shipment)


@router.get("/shipments")
def list_shipments(db: Session = Depends(database.get_db)):
    shipments = (
        db.query(models.Shipment)
        .options(load_only(*SHIPMENT_LIST_FIELDS))
        .order_by(models.Shipment.created_at.desc())
        .all()
    )
    return [
        logistics_service.serialize_shipment(shipment, include_route_coordinates=False)
        for shipment in shipments
    ]


@router.get("/shipments/{shipment_id}")
def get_shipment(shipment_id: int, db: Session = Depends(database.get_db)):
    shipment = db.query(models.Shipment).filter(models.Shipment.id == shipment_id).first()
    if shipment is None:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return logistics_service.serialize_shipment(shipment)


@router.post("/shipments/{shipment_id}/start")
def start_shipment(
    shipment_id: int,
    request: ShipmentStartRequest,
    db: Session = Depends(database.get_db),
):
    shipment = db.query(models.Shipment).filter(models.Shipment.id == shipment_id).first()
    if shipment is None:
        raise HTTPException(status_code=404, detail="Shipment not found")

    try:
        shipment = logistics_service.start_shipment(db, shipment)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    realtime_manager.ensure_tracking(shipment.id, request.tick_seconds)
    return logistics_service.serialize_shipment(shipment)


@router.delete("/shipments/{shipment_id}")
def delete_shipment(shipment_id: int, db: Session = Depends(database.get_db)):
    shipment = db.query(models.Shipment).filter(models.Shipment.id == shipment_id).first()
    if shipment is None:
        raise HTTPException(status_code=404, detail="Shipment not found")

    db.delete(shipment)
    db.commit()

    return {"success": True, "shipment_id": shipment_id}


@router.get("/tracking/{shipment_id}")
def get_tracking_logs(shipment_id: int, limit: int = 200, db: Session = Depends(database.get_db)):
    shipment = db.query(models.Shipment).filter(models.Shipment.id == shipment_id).first()
    if shipment is None:
        raise HTTPException(status_code=404, detail="Shipment not found")

    tracking_logs = _get_recent_tracking_logs(db, shipment_id, max(1, min(limit, 500)))

    return {
        "shipment": logistics_service.serialize_shipment(shipment),
        "logs": [logistics_service.serialize_tracking_log(log) for log in tracking_logs],
    }


@router.post("/carriers/create")
def create_carrier(carrier: CarrierCreate, db: Session = Depends(database.get_db)):
    record = models.Carrier(**carrier.dict())
    try:
        db.add(record)
        db.commit()
        db.refresh(record)
    except Exception as error:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Carrier creation failed: {error}") from error
    return record


@router.get("/carriers")
def list_carriers(db: Session = Depends(database.get_db)):
    return db.query(models.Carrier).all()


@router.post("/drivers/create")
def create_driver(driver: DriverCreate, db: Session = Depends(database.get_db)):
    record = models.Driver(**driver.dict())
    try:
        db.add(record)
        db.commit()
        db.refresh(record)
    except Exception as error:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Driver creation failed: {error}") from error
    return record


@router.get("/drivers")
def list_drivers(db: Session = Depends(database.get_db)):
    return db.query(models.Driver).all()


@router.websocket("/ws/shipments/{shipment_id}")
async def shipment_tracking_socket(websocket: WebSocket, shipment_id: int):
    db = database.SessionLocal()
    try:
        shipment = (
            db.query(models.Shipment)
            .options(load_only(*SHIPMENT_LIST_FIELDS))
            .filter(models.Shipment.id == shipment_id)
            .first()
        )
        if shipment is None:
            await websocket.close(code=4404)
            return

        await realtime_manager.connect(shipment_id, websocket)
        await websocket.send_json(
            {
                "type": "shipment.snapshot",
                "shipment": logistics_service.serialize_shipment(
                    shipment,
                    include_route_coordinates=False,
                ),
                "tracking": [
                    logistics_service.serialize_tracking_log(log)
                    for log in _get_recent_tracking_logs(db, shipment_id, 50)
                ],
            }
        )

        if shipment.status == "IN_TRANSIT":
            realtime_manager.ensure_tracking(shipment_id)

        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        realtime_manager.disconnect(shipment_id, websocket)
    finally:
        db.close()
