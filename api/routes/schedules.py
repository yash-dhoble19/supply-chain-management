from fastapi import APIRouter, Depends, HTTPException, Body, Path
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

import models
import database

router = APIRouter(prefix="/api/schedules", tags=["Schedules"])

class ScheduleRequestCreate(BaseModel):
    origin: str
    destination: str
    load_type: str = "STANDARD"
    distance_km: Optional[float] = None
    eta_hours: Optional[float] = None
    driver_id: int
    product_name: str
    quantity: int
    carrier_type: Optional[str] = None
    logistics_order_id: Optional[int] = None
    shipment_id: Optional[int] = None

class ScheduleRequestResponse(ScheduleRequestCreate):
    id: int
    status: str
    driver_name: Optional[str] = None
    created_at: datetime
    
    class Config:
        orm_mode = True

@router.post("/", response_model=ScheduleRequestResponse)
def create_schedule(req: ScheduleRequestCreate, db: Session = Depends(database.get_db)):
    # Look up the driver name using the User table (since drivers are now authenticating users)
    driver = db.query(models.User).filter(models.User.id == req.driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
        
    db_schedule = models.ScheduleRequest(
        origin=req.origin,
        destination=req.destination,
        load_type=req.load_type,
        distance_km=req.distance_km,
        eta_hours=req.eta_hours,
        driver_id=req.driver_id,
        driver_name=driver.name,
        product_name=req.product_name,
        quantity=req.quantity,
        carrier_type=req.carrier_type,
        logistics_order_id=req.logistics_order_id,
        shipment_id=req.shipment_id,
        status="PENDING",
        manufacturer_name="ChainMind Manufacturing"
    )
    
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    
    return db_schedule

@router.get("/", response_model=List[ScheduleRequestResponse])
def get_schedules(driver_id: Optional[int] = None, status: Optional[str] = None, db: Session = Depends(database.get_db)):
    query = db.query(models.ScheduleRequest)
    
    if driver_id is not None:
        query = query.filter(models.ScheduleRequest.driver_id == driver_id)
    if status is not None:
        query = query.filter(models.ScheduleRequest.status == status)
        
    return query.order_by(models.ScheduleRequest.created_at.desc()).all()

class UpdateStatusRequest(BaseModel):
    status: str # ACCEPTED, REJECTED, IN_PROGRESS, COMPLETED

@router.post("/{schedule_id}/status")
def update_schedule_status(schedule_id: int = Path(...), req: UpdateStatusRequest = Body(...), db: Session = Depends(database.get_db)):
    schedule = db.query(models.ScheduleRequest).filter(models.ScheduleRequest.id == schedule_id).first()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule request not found")
        
    schedule.status = req.status
    if req.status in ["ACCEPTED", "REJECTED"]:
        schedule.responded_at = datetime.utcnow()
    elif req.status == "COMPLETED":
        schedule.completed_at = datetime.utcnow()
        
    db.commit()
    db.refresh(schedule)
    
    # If accepted and linked to logistics order, update the order too
    if req.status == "ACCEPTED" and schedule.logistics_order_id:
        order = db.query(models.LogisticsOrder).filter(models.LogisticsOrder.id == schedule.logistics_order_id).first()
        if order:
            order.driver_id = schedule.driver_id
            order.status = "In Progress"
            db.commit()
            
    return {"success": True, "status": schedule.status, "id": schedule.id}
