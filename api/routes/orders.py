"""
Order routes — /orders/*
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import models
import database
from schemas.order import OrderCreate, OrderResponse
from services.background_tasks import generate_and_store_insight

router = APIRouter(tags=["Orders"])


def determine_order_risk(address: str) -> str:
    addr_lower = (address or "").lower()
    if any(k in addr_lower for k in ["p.o. box", "remote", "island", "rural", "international"]):
        return "HIGH RISK: Complex or remote delivery location."
    return "LOW RISK: Standard domestic delivery."

@router.post("/orders/", response_model=OrderResponse)
def create_order(order: OrderCreate, background_tasks: BackgroundTasks, db: Session = Depends(database.get_db)):
    risk = determine_order_risk(order.delivery_address)
    db_order = models.Order(**order.dict(), status="PENDING", ai_risk_assessment=risk)
    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    # Also create a logistics order entry for each product (simulate single product for now)
    # You can extend this for multiple products if needed
    db_logistics_order = models.LogisticsOrder(
        order_id=db_order.id,
        product_name=getattr(order, 'product_name', 'Unknown'),
        quantity=getattr(order, 'quantity', 1),
        unit_price=getattr(order, 'unit_price', 0.0),
        status="Pending"
    )
    db.add(db_logistics_order)
    db.commit()

    # Store the deterministic risk in the DB and then let AI improve it over time/save separate insight
    background_tasks.add_task(
        generate_and_store_insight,
        db=db,
        entity_type="ORDER",
        entity_id=str(db_order.id),
        insight_type="RISK_ANALYSIS",
        address=order.delivery_address
    )

    return db_order


@router.get("/orders/", response_model=List[OrderResponse])
def read_orders(db: Session = Depends(database.get_db)):
    return db.query(models.Order).all()
