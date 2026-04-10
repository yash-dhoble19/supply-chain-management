from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

import database
from models import DriverProfile, User
from api.auth_handler import get_current_user

router = APIRouter(prefix="/api/drivers", tags=["drivers"])

class DriverProfileSchema(BaseModel):
    driving_license: Optional[str] = None
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    license_plate: Optional[str] = None
    cost_per_km: Optional[float] = None

@router.get("/profile", response_model=DriverProfileSchema)
def get_driver_profile(db: Session = Depends(database.get_db), current_user: User = Depends(get_current_user)):
    if current_user.role.lower() != "driver":
        raise HTTPException(status_code=403, detail="Only drivers can have profiles")

    profile = db.query(DriverProfile).filter(DriverProfile.user_id == current_user.id).first()
    if not profile:
        return DriverProfileSchema() # Return empty default schema
    
    return {
        "driving_license": profile.driving_license,
        "vehicle_make": profile.vehicle_make,
        "vehicle_model": profile.vehicle_model,
        "license_plate": profile.license_plate,
        "cost_per_km": profile.cost_per_km
    }

@router.post("/profile", response_model=DriverProfileSchema)
def update_driver_profile(payload: DriverProfileSchema, db: Session = Depends(database.get_db), current_user: User = Depends(get_current_user)):
    if current_user.role.lower() != "driver":
        raise HTTPException(status_code=403, detail="Only drivers can have profiles")

    profile = db.query(DriverProfile).filter(DriverProfile.user_id == current_user.id).first()
    
    if not profile:
        profile = DriverProfile(user_id=current_user.id)
        db.add(profile)
    
    profile.driving_license = payload.driving_license
    profile.vehicle_make = payload.vehicle_make
    profile.vehicle_model = payload.vehicle_model
    profile.license_plate = payload.license_plate
    profile.cost_per_km = payload.cost_per_km

    db.commit()
    db.refresh(profile)

    return {
        "driving_license": profile.driving_license,
        "vehicle_make": profile.vehicle_make,
        "vehicle_model": profile.vehicle_model,
        "license_plate": profile.license_plate,
        "cost_per_km": profile.cost_per_km
    }

@router.get("/list")
def list_available_drivers(db: Session = Depends(database.get_db)):
    # Get all users with driver role
    drivers = db.query(User).filter(User.role.ilike("driver")).all()
    results = []
    for d in drivers:
        profile = db.query(DriverProfile).filter(DriverProfile.user_id == d.id).first()
        results.append({
            "id": d.id,
            "name": d.name,
            "cost_per_km": profile.cost_per_km if profile else None
        })
    return results
