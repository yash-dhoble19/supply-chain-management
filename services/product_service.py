"""
Product & Inventory service — single source of truth for stock logic.
"""
from datetime import datetime
from sqlalchemy.orm import Session
import models


def get_all_products(db: Session):
    return db.query(models.Product).all()


def get_product_by_id(db: Session, product_id: int):
    return db.query(models.Product).filter(models.Product.id == product_id).first()


def get_product_by_sku(db: Session, sku: str):
    return db.query(models.Product).filter(models.Product.sku == sku).first()


def create_product(db: Session, sku: str, name: str, category: str, stage: str,
                   current_stock: int, safety_stock_level: int, optimal_stock_level: int, unit_price: float):
    db_product = models.Product(
        sku=sku, name=name, category=category, stage=stage,
        current_stock=current_stock, safety_stock_level=safety_stock_level,
        optimal_stock_level=optimal_stock_level, unit_price=unit_price,
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


def update_product(db: Session, product: models.Product, **fields):
    for key, value in fields.items():
        if value is not None:
            setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product: models.Product):
    db.delete(product)
    db.commit()


def log_stock_movement(db: Session, product: models.Product, quantity_change: int, reason: str):
    product.current_stock += quantity_change
    log = models.InventoryLog(
        product_id=product.id,
        quantity_change=quantity_change,
        reason=reason,
        change_date=datetime.utcnow(),
    )
    db.add(log)
    db.commit()
    return product.current_stock


def analyze_inventory(db: Session) -> list[dict]:
    products = get_all_products(db)
    results = []
    for p in products:
        if p.current_stock < p.safety_stock_level:
            status, rec = "CRITICAL", "Replenish immediately."
        elif p.current_stock < (p.safety_stock_level * 1.2):
            status, rec = "LOW", "Plan Reorder soon."
        else:
            status, rec = "OK", "Optimal"

        results.append({
            "id": p.id, "product": p.name, "sku": p.sku,
            "on_hand": p.current_stock, "safety_stock": p.safety_stock_level,
            "optimal_stock": p.optimal_stock_level, "unit_price": p.unit_price,
            "category": p.category, "stage": p.stage,
            "status": status, "ai_recommendation": rec,
        })
    return results


def get_inventory_status(product) -> str:
    """Returns 'Critical', 'Low', or 'Healthy' for a product."""
    current = product.current_stock or 0
    safety = product.safety_stock_level or 0
    if current < safety:
        return "Critical"
    elif current < (safety * 1.2):
        return "Low"
    return "Healthy"
