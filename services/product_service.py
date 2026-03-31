"""
Product & Inventory service - single source of truth for stock logic.
"""
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

import models


def get_all_products(db: Session):
    return db.query(models.Product).all()


def get_inventory_source_records(db: Session):
    return get_all_products(db)


def get_product_by_id(db: Session, product_id: int):
    return db.query(models.Product).filter(models.Product.id == product_id).first()


def get_product_by_sku(db: Session, sku: str):
    return db.query(models.Product).filter(models.Product.sku == sku).first()


def create_product(
    db: Session,
    sku: str,
    name: str,
    category: str,
    stage: str,
    current_stock: int,
    safety_stock_level: int,
    optimal_stock_level: int,
    unit_price: float,
):
    db_product = models.Product(
        sku=sku,
        name=name,
        category=category,
        stage=stage,
        current_stock=current_stock,
        safety_stock_level=safety_stock_level,
        optimal_stock_level=optimal_stock_level,
        unit_price=unit_price,
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
    deleted = {
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
    db.delete(product)
    db.commit()
    return deleted


def get_inventory_metrics(db: Session):
    totals = db.query(
        func.coalesce(func.sum(models.Product.current_stock), 0).label("total_items"),
        func.coalesce(func.sum(models.Product.current_stock * models.Product.unit_price), 0.0).label("total_value"),
    ).one()

    total_items = int(totals.total_items or 0)
    total_value = float(round(totals.total_value or 0.0, 2))

    return {
        "total_items": total_items,
        "total_value": total_value,
    }


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

        results.append(
            {
                "id": p.id,
                "product": p.name,
                "sku": p.sku,
                "on_hand": p.current_stock,
                "safety_stock": p.safety_stock_level,
                "optimal_stock": p.optimal_stock_level,
                "unit_price": p.unit_price,
                "category": p.category,
                "stage": p.stage,
                "status": status,
                "ai_recommendation": rec,
            }
        )
    return results


def get_inventory_status(product) -> str:
    """Returns 'Critical', 'Low', or 'Healthy' for a product."""
    current = product.current_stock or 0
    safety = product.safety_stock_level or 0
    if current < safety:
        return "Critical"
    if current < (safety * 1.2):
        return "Low"
    return "OK"


def get_inventory_items(db: Session, page: int = 1, limit: int = 25, search: str | None = None):
    query = db.query(models.Product)

    if search:
        search_value = f"%{search.lower()}%"
        query = query.filter(
            models.Product.name.ilike(search_value)
            | models.Product.sku.ilike(search_value)
            | models.Product.category.ilike(search_value)
        )

    products = query.order_by(models.Product.name.asc()).offset((page - 1) * limit).limit(limit).all()

    all_po_items = (
        db.query(models.POItem)
        .join(models.PurchaseOrder)
        .filter(models.PurchaseOrder.status.in_(["DRAFT", "APPROVED", "IN_TRANSIT"]))
        .all()
    )

    po_items_by_product = {}
    for item in all_po_items:
        po_items_by_product.setdefault(item.product_id, []).append(item)

    items = []
    for product in products:
        pending_po_qty = 0
        in_transit_po_qty = 0
        product_po_items = po_items_by_product.get(product.id, [])
        for item in product_po_items:
            pending_po_qty += item.quantity_ordered
            if item.purchase_order and (item.purchase_order.status or "").upper() == "IN_TRANSIT":
                in_transit_po_qty += item.quantity_ordered

        stage = "WAREHOUSE"
        if in_transit_po_qty > 0:
            stage = "IN TRANSIT"
        elif pending_po_qty > 0:
            stage = "PRODUCTION"

        total_value = round((product.current_stock or 0) * (product.unit_price or 0), 2)
        status = get_inventory_status(product)
        capacity = 0.0
        if product.optimal_stock_level and product.optimal_stock_level > 0:
            capacity = min(100.0, round(((product.current_stock or 0) / product.optimal_stock_level) * 100, 2))

        items.append(
            {
                "id": product.id,
                "sku": product.sku,
                "name": product.name,
                "category": product.category,
                "stage": stage,
                "stock": product.current_stock or 0,
                "safety_stock_level": product.safety_stock_level or 0,
                "optimal_stock_level": product.optimal_stock_level or 0,
                "unit_price": product.unit_price or 0,
                "status": status,
                "capacity": capacity,
                "pending_po_qty": pending_po_qty,
                "in_transit_po_qty": in_transit_po_qty,
                "total_value": total_value,
            }
        )

    return items


def get_inventory_summary(db: Session):
    products = db.query(models.Product).all()

    total_on_hand = sum(p.current_stock or 0 for p in products)
    total_on_hand_value = round(sum((p.current_stock or 0) * (p.unit_price or 0) for p in products), 2)

    inbound_q = (
        db.query(models.POItem)
        .join(models.PurchaseOrder)
        .filter(models.PurchaseOrder.status.in_(["APPROVED", "IN_TRANSIT"]))
        .all()
    )
    total_inbound = sum(item.quantity_ordered or 0 for item in inbound_q)
    total_inbound_value = round(
        sum((item.quantity_ordered or 0) * (float(item.unit_price or 0)) for item in inbound_q),
        2,
    )

    total_items = total_on_hand + total_inbound
    total_value = round(total_on_hand_value + total_inbound_value, 2)
    critical_items = sum(1 for p in products if (p.current_stock or 0) < (p.safety_stock_level or 0))

    return {
        "total_items": total_items,
        "total_value": total_value,
        "critical_items": critical_items,
        "on_hand_items": total_on_hand,
        "on_hand_value": total_on_hand_value,
        "inbound_items": total_inbound,
        "inbound_value": total_inbound_value,
    }


def get_inventory_activity(db: Session, limit: int = 20):
    logs = (
        db.query(models.InventoryLog)
        .order_by(models.InventoryLog.change_date.desc(), models.InventoryLog.id.desc())
        .limit(limit)
        .all()
    )

    unique_logs = []
    seen_ids = set()
    for log in logs:
        if log.id in seen_ids:
            continue
        seen_ids.add(log.id)
        unique_logs.append(log)

    product_ids = [log.product_id for log in unique_logs]
    products = {product.id: product for product in db.query(models.Product).filter(models.Product.id.in_(product_ids)).all()}

    result = []
    for log in unique_logs:
        product = products.get(log.product_id)
        result.append(
            {
                "id": log.id,
                "product_id": log.product_id,
                "product_name": product.name if product else "Unknown",
                "sku": product.sku if product else "N/A",
                "change_date": log.change_date.isoformat() if log.change_date else None,
                "quantity_change": log.quantity_change,
                "reason": log.reason,
                "stockout_flag": bool(log.stockout_flag),
            }
        )

    return result


def adjust_inventory_stock(
    db: Session,
    product_id: int,
    target_stock: int | None,
    quantity_change: int | None,
    reason: str,
):
    product = get_product_by_id(db, product_id)
    if not product:
        return None

    current_stock = product.current_stock or 0

    if target_stock is not None:
        quantity_change = target_stock - current_stock
    if quantity_change is None:
        raise ValueError("quantity_change or target_stock required")

    product.current_stock = current_stock + quantity_change
    log = models.InventoryLog(
        product_id=product.id,
        quantity_change=quantity_change,
        reason=reason,
    )
    db.add(log)
    db.commit()
    db.refresh(product)
    return product
