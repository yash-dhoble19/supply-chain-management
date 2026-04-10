# Accept job endpoint
from fastapi import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi import Body
import models
import database
from pydantic import BaseModel
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Body, Path

router = APIRouter(tags=["LogisticsOrders"])
class AcceptJobRequest(BaseModel):
    driver_id: int

# Accept a job (assign driver_id)
@router.post("/logistics/orders/{order_id}/accept")
def accept_logistics_order(order_id: int = Path(...), req: AcceptJobRequest = Body(...), db: Session = Depends(database.get_db)):
    order = db.query(models.LogisticsOrder).filter(models.LogisticsOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    # Add driver_id column if not present
    if not hasattr(order, "driver_id"):
        # This is a migration issue; inform user
        raise HTTPException(status_code=500, detail="driver_id column missing in LogisticsOrder. Please add it to the database.")
    order.driver_id = req.driver_id
    order.status = "In Progress"
    db.commit()
    db.refresh(order)
    return {"success": True, "order_id": order.id}



from pydantic import BaseModel
# Response schema including supplier details
class LogisticsOrderWithSupplier(BaseModel):
    id: int
    order_id: Optional[int]
    product_name: str
    quantity: int
    status: Optional[str]
    driver_id: Optional[int]
    retailer_name: Optional[str]
    retailer_email: Optional[str]
    retailer_phone: Optional[str]
    retailer_location: Optional[str]
    sku: Optional[str]
    imageUrl: Optional[str]
    supplierName: Optional[str]
    current_location_lat: Optional[float]
    current_location_lon: Optional[float]
    # Payment tracking
    payment_status: Optional[str]
    upi_transaction_id: Optional[str]
    # Supplier details
    supplierEmail: Optional[str]
    supplierMobile: Optional[str]
    supplierCompany: Optional[str]

    class Config:
        orm_mode = True

@router.get("/logistics/orders/", response_model=List[LogisticsOrderWithSupplier])
def get_logistics_orders(
    status: Optional[str] = None,
    driver_id: Optional[int] = None,
    unassigned: Optional[bool] = None,
    db: Session = Depends(database.get_db),
):
    query = db.query(models.LogisticsOrder)

    if status:
        query = query.filter(models.LogisticsOrder.status == status)
    if driver_id is not None:
        query = query.filter(models.LogisticsOrder.driver_id == driver_id)
    if unassigned is True:
        query = query.filter(models.LogisticsOrder.driver_id == None)

    orders = query.order_by(models.LogisticsOrder.created_at.desc()).all()
    results = []
    for order in orders:
        # Try to find supplier by name
        supplier = None
        if order.supplierName:
            supplier = db.query(models.Supplier).filter(models.Supplier.name == order.supplierName).first()
        results.append({
            "id": order.id,
            "order_id": order.order_id,
            "product_name": order.product_name,
            "quantity": order.quantity,
            "status": order.status,
            "driver_id": order.driver_id,
            "retailer_name": order.retailer_name,
            "retailer_email": order.retailer_email,
            "retailer_phone": order.retailer_phone,
            "retailer_location": order.retailer_location,
            "sku": order.sku,
            "imageUrl": order.imageUrl,
            "supplierName": order.supplierName,
            "current_location_lat": order.current_location_lat,
            "current_location_lon": order.current_location_lon,
            "payment_status": getattr(order, "payment_status", None),
            "upi_transaction_id": getattr(order, "upi_transaction_id", None),
            "supplierEmail": supplier.contact_email if supplier else None,
            "supplierMobile": getattr(supplier, "mobile", None) if supplier and hasattr(supplier, "mobile") else None,
            "supplierCompany": getattr(supplier, "company_name", None) if supplier and hasattr(supplier, "company_name") else None,
        })
    return results

@router.post("/logistics/orders/{order_id}/source-driver")
def source_logistics_order(order_id: int = Path(...), db: Session = Depends(database.get_db)):
    order = db.query(models.LogisticsOrder).filter(models.LogisticsOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.driver_id is not None:
        raise HTTPException(status_code=400, detail="Order is already assigned to a driver.")
    order.status = "Sourced"
    db.commit()
    db.refresh(order)
    return {"success": True, "order_id": order.id}


class LogisticsOrderLocationUpdate(BaseModel):
    current_location_lat: float
    current_location_lon: float


@router.post("/logistics/orders/{order_id}/update-location")
def update_logistics_order_location(
    order_id: int = Path(...),
    req: LogisticsOrderLocationUpdate = Body(...),
    db: Session = Depends(database.get_db),
):
    order = db.query(models.LogisticsOrder).filter(models.LogisticsOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.driver_id is None:
        raise HTTPException(status_code=400, detail="Cannot update location for an unassigned order")

    order.current_location_lat = req.current_location_lat
    order.current_location_lon = req.current_location_lon
    db.commit()
    db.refresh(order)
    return {"success": True, "order_id": order.id}

# Pydantic schema for input validation
class LogisticsOrderCreate(BaseModel):
    product_name: str
    sku: str = None
    quantity: int
    unit_price: float
    category: str = None
    notes: str = None
    imageUrl: str = None
    supplierName: str = None
    publishedAt: str = None
    current_location_lat: float = None
    current_location_lon: float = None
    status: str = "Pending"
    retailer_name: str = None
    retailer_email: str = None
    retailer_phone: str = None
    retailer_location: str = None
    driver_id: Optional[int] = None
    payment_status: Optional[str] = None
    upi_transaction_id: Optional[str] = None

@router.post("/logistics/orders/create")
def create_logistics_order(order: LogisticsOrderCreate = Body(...), db: Session = Depends(database.get_db)):
    db_order = models.LogisticsOrder(
        product_name=order.product_name,
        quantity=order.quantity,
        unit_price=order.unit_price,
        status=order.status,
        driver_id=order.driver_id,
        retailer_name=order.retailer_name,
        retailer_email=order.retailer_email,
        retailer_phone=order.retailer_phone,
        retailer_location=order.retailer_location,
        sku=order.sku,
        category=order.category,
        notes=order.notes,
        imageUrl=order.imageUrl,
        supplierName=order.supplierName,
        publishedAt=order.publishedAt,
        payment_status=order.payment_status,
        upi_transaction_id=order.upi_transaction_id,
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order
# anything
