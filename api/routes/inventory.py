from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import database
import models
from schemas.inventory import InventoryAdjustment
from services.product_service import (
    get_inventory_items,
    get_inventory_total_count,
    get_inventory_summary,
    get_inventory_activity,
    adjust_inventory_stock,
    get_product_by_id,
)

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])


@router.get("/bootstrap")
def inventory_bootstrap(
    page: int = 1,
    limit: int = 25,
    search: Optional[str] = None,
    db: Session = Depends(database.get_db),
):
    items = get_inventory_items(db, page=page, limit=limit, search=search)
    total = get_inventory_total_count(db, search=search)
    return {
        "inventory": {
            "page": page,
            "limit": limit,
            "total": total,
            "items": items,
        },
        "summary": get_inventory_summary(db),
        "activity": get_inventory_activity(db, limit=20),
    }


@router.get("/")
def list_inventory(
    page: int = 1,
    limit: int = 25,
    search: Optional[str] = None,
    db: Session = Depends(database.get_db),
):
    items = get_inventory_items(db, page=page, limit=limit, search=search)
    total = get_inventory_total_count(db, search=search)
    return {
        "page": page,
        "limit": limit,
        "total": total,
        "items": items,
    }


@router.get("/summary")
def inventory_summary(db: Session = Depends(database.get_db)):
    return get_inventory_summary(db)


@router.patch("/{product_id}")
def update_inventory(product_id: int, adjustment: InventoryAdjustment, db: Session = Depends(database.get_db)):
    product = get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    try:
        updated = adjust_inventory_stock(
            db,
            product_id=product_id,
            target_stock=adjustment.target_stock,
            quantity_change=adjustment.quantity_change,
            reason=adjustment.reason,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not updated:
        raise HTTPException(status_code=500, detail="Could not update inventory")

    return {"message": "Inventory updated", "product_id": product_id, "current_stock": updated.current_stock}


@router.get("/activity")
def inventory_activity(limit: int = 20, db: Session = Depends(database.get_db)):
    return get_inventory_activity(db, limit=limit)
