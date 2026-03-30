"""
Product & Inventory routes — /products/*, /inventory/*
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import database
from schemas.product import ProductCreate, ProductUpdate, StockMovement
from services import product_service

router = APIRouter(tags=["Products & Inventory"])


@router.post("/products/")
def create_product(product: ProductCreate, db: Session = Depends(database.get_db)):
    existing = product_service.get_product_by_sku(db, product.sku)
    if existing:
        raise HTTPException(status_code=400, detail="SKU exists")
    db_product = product_service.create_product(db, **product.dict())
    return {"message": "Created", "id": db_product.id}


@router.put("/products/{product_id}")
def update_product(product_id: int, product: ProductUpdate, db: Session = Depends(database.get_db)):
    db_product = product_service.get_product_by_id(db, product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    update_fields = {k: v for k, v in product.dict().items() if v is not None}
    product_service.update_product(db, db_product, **update_fields)
    return {"message": "Updated"}


@router.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(database.get_db)):
    db_product = product_service.get_product_by_id(db, product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    product_service.delete_product(db, db_product)
    return {"message": "Product deleted"}


@router.post("/inventory/logs")
def log_stock_movement(movement: StockMovement, db: Session = Depends(database.get_db)):
    product = product_service.get_product_by_id(db, movement.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    new_stock = product_service.log_stock_movement(db, product, movement.quantity_change, movement.reason)
    return {"message": "Stock updated", "new_stock": new_stock}


@router.get("/inventory/analysis")
def analyze_inventory(db: Session = Depends(database.get_db)):
    return product_service.analyze_inventory(db)
