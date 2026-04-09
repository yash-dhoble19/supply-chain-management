"""
Product & Inventory routes — /products/*, /inventory/*
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging
import database
from schemas.product import ProductCreate, ProductUpdate, StockMovement
from services import product_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Products & Inventory"])


def _product_as_dict(product):
    return {
        "id": product.id,
        "sku": product.sku,
        "name": product.name,
        "category": product.category,
        "stage": product.stage,
        "current_stock": product.current_stock,
        "safety_stock_level": product.safety_stock_level,
        "optimal_stock_level": product.optimal_stock_level,
        "unit_price": product.unit_price,
    }


@router.post("/products/")
@router.post("/products")
def create_product(product: ProductCreate, db: Session = Depends(database.get_db)):
    logger.info("Create product request: %s", product.dict())
    existing = product_service.get_product_by_sku(db, product.sku)
    if existing:
        logger.warning("Create product failed: SKU exists %s", product.sku)
        raise HTTPException(status_code=400, detail="SKU exists")
    db_product = product_service.create_product(db, **product.dict())
    product_data = _product_as_dict(db_product)
    logger.info("Created product response: %s", product_data)
    return {"message": "Created", "product": product_data}


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
    logger.info("Delete product request: %s", product_id)
    db_product = product_service.get_product_by_id(db, product_id)
    if not db_product:
        logger.warning("Delete product failed: not found %s", product_id)
        raise HTTPException(status_code=404, detail="Product not found")

    deleted = product_service.delete_product(db, db_product)
    logger.info("Deleted product response: %s", deleted)
    return {"message": "Product deleted", "product": deleted}


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

# anything
