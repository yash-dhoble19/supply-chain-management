"""
Procurement service - supplier scoring, insights, and PO lifecycle.
Single source of truth for procurement business logic.
"""
import re
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session, joinedload

import models


PURCHASE_ORDER_TAX_RATE = 18.0
PURCHASE_ORDER_COMPANY = {
    "companyName": "ChainMind Supply Intelligence",
    "companyAddress": "Procurement Operations, Innovation District, Pune, India",
    "billToCompany": "ChainMind Manufacturing Group",
    "billToAddress": "Accounts Payable, Global Supply Tower, Pune, India",
    "contactEmail": "procurement@chainmind.ai",
}


def get_supplier_reliability_percent(supplier) -> float:
    reliability = supplier.reliability_percent
    if reliability is None:
        reliability = supplier.reliability_score or 0
    return round(max(0.0, min(100.0, float(reliability))), 1)


def get_supplier_on_time_percent(supplier) -> float:
    on_time = supplier.on_time_delivery_percent
    if on_time is None:
        on_time = get_supplier_reliability_percent(supplier) - 1.5
    return round(max(0.0, min(100.0, float(on_time))), 1)


def get_supplier_average_delivery_days(supplier) -> int:
    return int(
        supplier.average_delivery_days
        or supplier.delivery_speed_days
        or supplier.lead_time_days
        or 0
    )


def get_supplier_unit_price(supplier) -> float:
    return round(float(supplier.unit_price or supplier.price_per_unit or 0.0), 2)


def compose_supplier_location(supplier) -> str:
    location_parts = [supplier.city, supplier.state, supplier.country]
    location = ", ".join([part for part in location_parts if part])
    return location or supplier.address or "Location pending"


def normalize_supplier_status(status: Optional[str]) -> str:
    normalized = (status or "ACTIVE").strip().upper().replace(" ", "_")
    if normalized in {"BLOCKED", "INACTIVE", "AT_RISK"}:
        return normalized
    return "ACTIVE"


def get_supplier_display_status(supplier) -> str:
    if supplier.preferred_supplier:
        return "Preferred"
    return normalize_supplier_status(supplier.status).replace("_", " ").title()


def get_supplier_performance_tier(score: float) -> str:
    if score >= 95:
        return "Elite"
    if score >= 88:
        return "Strong"
    if score >= 78:
        return "Stable"
    return "Watch"


def calculate_supplier_score(supplier, product_price=None) -> float:
    reliability_norm = get_supplier_reliability_percent(supplier) / 100
    lead_time_norm = max(0, 1 - (get_supplier_average_delivery_days(supplier) / 30))
    supplier_unit_price = get_supplier_unit_price(supplier)
    comparison_price = max(product_price or supplier_unit_price or 1, 1)
    price_norm = max(0, 1 - (supplier_unit_price / (comparison_price * 2))) if supplier_unit_price else 0.7
    score = (reliability_norm * 0.4) + (lead_time_norm * 0.3) + (price_norm * 0.3)
    return round(score * 100, 2)


def find_best_supplier_for_product(product, db: Session):
    suppliers = db.query(models.Supplier).filter(
        models.Supplier.category == product.category
    ).all()
    if not suppliers:
        suppliers = db.query(models.Supplier).all()
    if not suppliers:
        return None

    supplier_scores = [
        {"supplier": supplier, "score": calculate_supplier_score(supplier, product.unit_price)}
        for supplier in suppliers
    ]
    best = max(supplier_scores, key=lambda item: item["score"])
    return best["supplier"]


def calculate_supply_chain_health_score(db: Session) -> float:
    products = db.query(models.Product).all()
    suppliers = db.query(models.Supplier).all()
    pending_pos = db.query(models.PurchaseOrder).filter(
        models.PurchaseOrder.status == "DRAFT"
    ).count()

    critical_items = sum(1 for product in products if product.current_stock < (product.optimal_stock_level * 0.2))
    critical_penalty = min(critical_items * 5, 40)
    po_penalty = min(pending_pos * 3, 20)
    avg_reliability = sum(get_supplier_reliability_percent(supplier) for supplier in suppliers) / len(suppliers) if suppliers else 90
    supplier_bonus = (avg_reliability - 80) / 2
    return max(0, min(100, 100 - critical_penalty - po_penalty + supplier_bonus))


def generate_morning_briefing(health_score: float, critical_count: int, pending_pos: int, critical_names: list) -> str:
    if health_score < 60:
        text = "Supply chain health is highly critical."
    elif health_score < 80:
        text = "Supply chain health requires attention."
    else:
        text = "Supply chain operations are stable."

    critical_str = f" Immediate action needed on {', '.join(critical_names)}." if critical_names else ""
    return f"{text} Currently tracking {pending_pos} pending purchase orders. You have {critical_count} critical inventory items.{critical_str}"


def generate_urgency_reasoning(product, supplier, has_active_po=False, po_status=None) -> str:
    stock_pct = (product.current_stock / product.optimal_stock_level * 100) if product.optimal_stock_level > 0 else 0
    if has_active_po:
        verb = "Approved" if po_status == "APPROVED" else "In Transit" if po_status == "IN_TRANSIT" else "Drafted"
        return f"A Purchase Order is currently {verb}. Stock remains at {stock_pct:.0f}% pending delivery."
    if stock_pct < 20:
        return f"Stock critically low at {stock_pct:.0f}%. We recommend immediate replenishment from {supplier.name}."
    if stock_pct < 35:
        return f"Stock dropping ({stock_pct:.0f}%). Consider ordering from {supplier.name} soon to avoid stockouts."
    return f"Stock is stable at {stock_pct:.0f}%."


def _supplier_products_supplied(supplier) -> list[str]:
    seen = set()
    products = []
    for value in [supplier.product_name] + [po.product_name for po in supplier.purchase_orders if po.product_name]:
        cleaned = (value or "").strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            products.append(cleaned)
    return products


def serialize_supplier_record(supplier) -> dict:
    score = round(supplier.supplier_score or calculate_supplier_score(supplier), 1)
    reliability = get_supplier_reliability_percent(supplier)
    on_time = get_supplier_on_time_percent(supplier)
    total_spend = round(
        sum(float(po.total_value or po.total_amount or 0) for po in supplier.purchase_orders),
        2,
    )
    total_orders = len(supplier.purchase_orders)
    products_supplied = _supplier_products_supplied(supplier)

    return {
        "supplier_id": str(supplier.id),
        "supplier_name": supplier.name,
        "supplier_code": supplier.supplier_code or f"SUP-{supplier.id:04d}",
        "company_name": supplier.company_name or supplier.name,
        "contact_person": supplier.contact_person,
        "email": supplier.contact_email,
        "phone": supplier.phone,
        "website": supplier.website,
        "product_name": supplier.product_name or (products_supplied[0] if products_supplied else "Product pending"),
        "product_category": supplier.product_category or supplier.category or "General",
        "supplied_products": products_supplied,
        "unit_price": get_supplier_unit_price(supplier),
        "currency": supplier.currency or "USD",
        "delivery_cost": round(float(supplier.delivery_cost or 0.0), 2),
        "average_delivery_days": get_supplier_average_delivery_days(supplier),
        "minimum_order_quantity": supplier.minimum_order_quantity,
        "supplier_score": score,
        "reliability_percent": reliability,
        "on_time_delivery_percent": on_time,
        "total_orders": total_orders,
        "total_spend": total_spend,
        "status": get_supplier_display_status(supplier),
        "raw_status": normalize_supplier_status(supplier.status),
        "preferred_supplier": bool(supplier.preferred_supplier),
        "supplier_type": supplier.supplier_type or "Strategic",
        "address": supplier.address,
        "location": compose_supplier_location(supplier),
        "city": supplier.city,
        "state": supplier.state,
        "country": supplier.country,
        "postal_code": supplier.postal_code,
        "gst_number": supplier.gst_number,
        "tax_id": supplier.tax_id,
        "notes": supplier.notes,
        "performance_tier": get_supplier_performance_tier(score),
        "created_at": supplier.created_at.isoformat() if supplier.created_at else None,
        "updated_at": supplier.updated_at.isoformat() if supplier.updated_at else None,
    }


def _assign_supplier_fields(db_supplier, payload) -> None:
    db_supplier.name = payload.supplier_name.strip()
    db_supplier.company_name = (payload.company_name or payload.supplier_name).strip()
    db_supplier.contact_person = payload.contact_person
    db_supplier.contact_email = payload.email.strip()
    db_supplier.phone = payload.phone
    db_supplier.website = payload.website

    db_supplier.product_name = payload.product_name
    db_supplier.product_category = payload.product_category or "General"
    db_supplier.category = payload.product_category or db_supplier.category or "General"

    db_supplier.unit_price = payload.unit_price
    db_supplier.price_per_unit = payload.unit_price
    db_supplier.currency = payload.currency or "USD"
    db_supplier.delivery_cost = payload.delivery_cost
    db_supplier.average_delivery_days = payload.average_delivery_days
    db_supplier.delivery_speed_days = payload.average_delivery_days
    db_supplier.lead_time_days = payload.average_delivery_days
    db_supplier.minimum_order_quantity = payload.minimum_order_quantity

    db_supplier.supplier_type = payload.supplier_type or "Strategic"
    db_supplier.status = normalize_supplier_status(payload.status)
    db_supplier.preferred_supplier = payload.preferred_supplier

    db_supplier.address = payload.address
    db_supplier.city = payload.city
    db_supplier.state = payload.state
    db_supplier.country = payload.country
    db_supplier.postal_code = payload.postal_code

    db_supplier.gst_number = payload.gst_number
    db_supplier.tax_id = payload.tax_id
    db_supplier.notes = payload.notes

    db_supplier.reliability_percent = payload.reliability_percent
    db_supplier.reliability_score = payload.reliability_percent
    db_supplier.on_time_delivery_percent = payload.on_time_delivery_percent
    db_supplier.supplier_score = payload.supplier_score or calculate_supplier_score(db_supplier, payload.unit_price)


def create_supplier(db: Session, payload):
    db_supplier = models.Supplier()
    _assign_supplier_fields(db_supplier, payload)
    db.add(db_supplier)
    db.commit()
    db.refresh(db_supplier)

    if not db_supplier.supplier_code:
        db_supplier.supplier_code = payload.supplier_code or f"SUP-{db_supplier.id:04d}"
        db.commit()
        db.refresh(db_supplier)

    return db_supplier


def update_supplier(db: Session, db_supplier, payload):
    _assign_supplier_fields(db_supplier, payload)
    if payload.supplier_code:
        db_supplier.supplier_code = payload.supplier_code
    elif not db_supplier.supplier_code:
        db_supplier.supplier_code = f"SUP-{db_supplier.id:04d}"
    db.commit()
    db.refresh(db_supplier)
    return db_supplier


def get_supplier_by_name(db: Session, name: str):
    return db.query(models.Supplier).filter(models.Supplier.name == name).first()


def get_supplier_by_code(db: Session, supplier_code: str):
    return db.query(models.Supplier).filter(models.Supplier.supplier_code == supplier_code).first()


def get_supplier_by_id(db: Session, supplier_id: int):
    return db.query(models.Supplier).filter(models.Supplier.id == supplier_id).first()


def get_all_suppliers(db: Session):
    return (
        db.query(models.Supplier)
        .options(joinedload(models.Supplier.purchase_orders).joinedload(models.PurchaseOrder.items))
        .order_by(models.Supplier.created_at.desc().nullslast(), models.Supplier.id.desc())
        .all()
    )


def build_supplier_management_records(db: Session) -> list[dict]:
    return [serialize_supplier_record(supplier) for supplier in get_all_suppliers(db)]


def get_supplier_management_detail(db: Session, supplier_id: int) -> Optional[dict]:
    supplier = (
        db.query(models.Supplier)
        .options(joinedload(models.Supplier.purchase_orders).joinedload(models.PurchaseOrder.items))
        .filter(models.Supplier.id == supplier_id)
        .first()
    )
    if not supplier:
        return None

    record = serialize_supplier_record(supplier)
    recent_purchase_orders = sorted(
        supplier.purchase_orders,
        key=lambda po: po.created_at or datetime.min,
        reverse=True,
    )[:5]
    record["recent_purchase_orders"] = [
        {
            "id": str(po.id),
            "po_number": po.po_number,
            "product_name": po.product_name or "Procurement Order",
            "status": normalize_po_status(po.status),
            "priority": (po.priority or "Medium").title(),
            "total_value": round(float(po.total_value or po.total_amount or 0), 2),
            "created_at": po.created_at.isoformat() if po.created_at else None,
            "expected_delivery": po.expected_delivery.isoformat() if po.expected_delivery else None,
        }
        for po in recent_purchase_orders
    ]
    return record


def build_supplier_analysis(db: Session) -> list[dict]:
    suppliers = get_all_suppliers(db)
    analysis = []
    for supplier in suppliers:
        on_time_rate = get_supplier_on_time_percent(supplier)
        overall_score = calculate_supplier_score(supplier)
        reliability = get_supplier_reliability_percent(supplier)

        if supplier.preferred_supplier or (reliability >= 85 and on_time_rate >= 80):
            verdict = "Partner"
        elif normalize_supplier_status(supplier.status) in {"BLOCKED", "AT_RISK"} or reliability < 70 or on_time_rate < 60:
            verdict = "At Risk"
        else:
            verdict = "Vetted"

        quality_proxy = round(
            min(100.0, (reliability * 0.7) + (on_time_rate * 0.3)),
            1,
        )

        analysis.append({
            "id": str(supplier.id),
            "name": supplier.name,
            "location": compose_supplier_location(supplier),
            "verdict": verdict,
            "score": overall_score,
            "reliability": reliability,
            "onTimeDelivery": on_time_rate,
            "qualityRate": quality_proxy,
            "deliverySpeedDays": get_supplier_average_delivery_days(supplier),
            "pricePerUnit": get_supplier_unit_price(supplier),
        })
    return analysis


def build_procurement_insights(db: Session, limit: int = 10) -> list[dict]:
    products = db.query(models.Product).all()
    all_suppliers = db.query(models.Supplier).all()
    suppliers_by_category = {}
    for supplier in all_suppliers:
        suppliers_by_category.setdefault(supplier.category, []).append(supplier)

    active_pos = (
        db.query(models.PurchaseOrder)
        .options(joinedload(models.PurchaseOrder.items))
        .filter(models.PurchaseOrder.status.in_(["DRAFT", "APPROVED", "IN_TRANSIT"]))
        .order_by(models.PurchaseOrder.created_at.desc())
        .all()
    )

    pos_by_product = {}
    for po in active_pos:
        for item in po.items:
            pos_by_product.setdefault(item.product_id, []).append(po)

    insights = []
    for product in products:
        if product.optimal_stock_level <= 0:
            continue

        candidates = suppliers_by_category.get(product.category, all_suppliers)
        if not candidates:
            continue

        scored = [{"supplier": supplier, "score": calculate_supplier_score(supplier, product.unit_price)} for supplier in candidates]
        best_supplier = max(scored, key=lambda item: item["score"])["supplier"]

        product_active_pos = pos_by_product.get(product.id, [])
        product_active_pos = sorted(list(set(product_active_pos)), key=lambda po: (po.created_at or datetime.min), reverse=True)

        has_active_po = len(product_active_pos) > 0
        latest_po = product_active_pos[0] if has_active_po else None

        incoming_qty = sum(
            item.quantity_ordered for po in product_active_pos for item in po.items if item.product_id == product.id
        )
        effective_stock_pct = ((product.current_stock + incoming_qty) / max(product.optimal_stock_level, 1) * 100)
        stock_pct = (product.current_stock / max(product.optimal_stock_level, 1) * 100)

        if effective_stock_pct >= 60 and not has_active_po:
            continue

        if effective_stock_pct < 20:
            priority = "urgent"
        elif effective_stock_pct < 35:
            priority = "high"
        else:
            priority = "monitor"

        if has_active_po:
            status_str = latest_po.status
            action_label = {"DRAFT": "PO Drafted", "APPROVED": "PO Approved", "IN_TRANSIT": "In Transit"}.get(status_str, "PO Active")
            action_type = "view_po"
        else:
            action_label = "Quick PO" if priority in ["urgent", "high"] else "Draft Email"
            action_type = "quick_po" if priority in ["urgent", "high"] else "draft_email"

        replenishment_qty = max(0, product.optimal_stock_level - (product.current_stock + incoming_qty))
        if replenishment_qty == 0 and has_active_po:
            replenishment_qty = incoming_qty

        supplier_unit_price = round(best_supplier.price_per_unit or best_supplier.unit_price or product.unit_price or 0, 2)
        supplier_score = calculate_supplier_score(best_supplier, supplier_unit_price)
        estimated_cost = round(replenishment_qty * supplier_unit_price, 2)

        reasoning = generate_urgency_reasoning(
            product,
            best_supplier,
            has_active_po,
            latest_po.status if latest_po else None,
        )

        insights.append({
            "id": str(product.id),
            "productId": product.id,
            "supplierId": best_supplier.id,
            "sku": product.sku,
            "title": product.name,
            "priority": priority,
            "reasoning": reasoning,
            "unitPrice": supplier_unit_price,
            "supplierScore": supplier_score,
            "estimatedLeadTime": f"{get_supplier_average_delivery_days(best_supplier)} Days",
            "estimatedLeadTimeDays": get_supplier_average_delivery_days(best_supplier),
            "replenishmentQty": replenishment_qty,
            "actionLabel": action_label,
            "actionType": action_type,
            "supplierName": best_supplier.name,
            "estimatedCost": estimated_cost,
        })

    priority_order = {"urgent": 0, "high": 1, "monitor": 2, "normal": 3}
    insights.sort(key=lambda item: (priority_order.get(item["priority"], 3), item["estimatedLeadTimeDays"]))
    return insights[:limit]


def generate_po_number(db: Session) -> str:
    count = db.query(models.PurchaseOrder).count()
    return f"PO-{datetime.now().strftime('%Y%m')}-{count + 1:04d}"


def extract_lead_time_days(estimated_lead_time: Optional[str], fallback_days: int) -> int:
    if estimated_lead_time:
        match = re.search(r"(\d+)", estimated_lead_time)
        if match:
            return max(int(match.group(1)), 1)
    return max(fallback_days or 1, 1)


def create_purchase_order(*, supplier, product, product_name: str, quantity: int,
                          unit_price: float, priority: str, estimated_lead_time: Optional[str], db: Session):
    po_number = generate_po_number(db)
    lead_time_days = extract_lead_time_days(estimated_lead_time, get_supplier_average_delivery_days(supplier))
    expected_delivery = datetime.utcnow() + timedelta(days=lead_time_days)
    total_value = round(quantity * unit_price, 2)

    db_po = models.PurchaseOrder(
        po_number=po_number,
        supplier_id=supplier.id,
        product_name=product_name,
        quantity=quantity,
        total_value=total_value,
        total_amount=Decimal(str(total_value)),
        priority=priority.title(),
        status="DRAFT",
        expected_delivery=expected_delivery,
        expected_delivery_date=expected_delivery.date(),
    )
    db.add(db_po)
    db.commit()
    db.refresh(db_po)

    po_item = models.POItem(
        po_id=db_po.id,
        product_id=product.id,
        quantity_ordered=quantity,
        unit_price=Decimal(str(round(unit_price, 2))),
    )
    db.add(po_item)
    db.commit()
    db.refresh(db_po)
    return db_po


def normalize_po_status(status: str) -> str:
    normalized = (status or "DRAFT").strip().upper()
    return {"DRAFT": "draft", "APPROVED": "approved", "IN_TRANSIT": "in_transit", "RECEIVED": "received"}.get(normalized, "draft")


def update_po_status(db: Session, db_po, new_status: str):
    db_po.status = new_status

    if new_status == "RECEIVED":
        po_items = db.query(models.POItem).filter(models.POItem.po_id == db_po.id).all()
        for item in po_items:
            product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
            if product:
                product.current_stock += item.quantity_ordered
                log = models.InventoryLog(
                    product_id=product.id,
                    quantity_change=item.quantity_ordered,
                    reason=f"PO Received: {db_po.po_number}",
                    change_date=datetime.utcnow(),
                )
                db.add(log)

    db.commit()
    db.refresh(db_po)
    return db_po


def resolve_procurement_context(db: Session, product_id=None, sku=None, supplier_id=None, supplier_name=None):
    product = None
    supplier = None

    if product_id is not None:
        product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if product is None and sku:
        product = db.query(models.Product).filter(models.Product.sku == sku).first()

    if supplier_id is not None:
        supplier = db.query(models.Supplier).filter(models.Supplier.id == supplier_id).first()
    if supplier is None and supplier_name:
        supplier = db.query(models.Supplier).filter(models.Supplier.name == supplier_name).first()

    return product, supplier


def build_purchase_order_document(db_po, db: Session) -> dict:
    supplier = db.query(models.Supplier).filter(models.Supplier.id == db_po.supplier_id).first()
    po_items = db.query(models.POItem).filter(models.POItem.po_id == db_po.id).all()

    items = []
    subtotal = 0.0
    for item in po_items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        rate = float(item.unit_price or 0)
        quantity = item.quantity_ordered or 0
        amount = round(quantity * rate, 2)
        subtotal += amount
        items.append({
            "description": product.name if product else (db_po.product_name or "Procurement item"),
            "sku": product.sku if product else "N/A",
            "quantity": quantity,
            "rate": rate,
            "amount": amount,
        })

    if not items:
        fallback_amount = float(db_po.total_amount or db_po.total_value or 0)
        fallback_rate = round(fallback_amount / max(db_po.quantity or 1, 1), 2) if fallback_amount else 0.0
        items.append({
            "description": db_po.product_name or "Procurement item",
            "sku": "N/A",
            "quantity": db_po.quantity or 0,
            "rate": fallback_rate,
            "amount": fallback_amount,
        })
        subtotal = fallback_amount

    subtotal = round(subtotal, 2)
    tax = round(subtotal * (PURCHASE_ORDER_TAX_RATE / 100), 2)
    total = round(subtotal + tax, 2)
    created_at = db_po.created_at or datetime.utcnow()
    expected_delivery = db_po.expected_delivery or (
        datetime.combine(db_po.expected_delivery_date, datetime.min.time())
        if db_po.expected_delivery_date else None
    )

    return {
        "id": str(db_po.id),
        "poNumber": db_po.po_number,
        "issueDate": created_at.isoformat(),
        "deliveryDate": expected_delivery.isoformat() if expected_delivery else None,
        "status": normalize_po_status(db_po.status),
        "supplierName": supplier.name if supplier else "Unknown supplier",
        "supplierAddress": compose_supplier_location(supplier) if supplier else "Supplier address pending",
        "supplierEmail": supplier.contact_email if supplier else PURCHASE_ORDER_COMPANY["contactEmail"],
        "companyName": PURCHASE_ORDER_COMPANY["companyName"],
        "companyAddress": PURCHASE_ORDER_COMPANY["companyAddress"],
        "billToCompany": PURCHASE_ORDER_COMPANY["billToCompany"],
        "billToAddress": PURCHASE_ORDER_COMPANY["billToAddress"],
        "priority": db_po.priority or "Medium",
        "notes": (
            f"Auto-generated from procurement insight workflow. Priority: {db_po.priority}. "
            "Please confirm supplier availability before dispatch."
        ),
        "subtotal": subtotal,
        "taxRate": PURCHASE_ORDER_TAX_RATE,
        "tax": tax,
        "total": total,
        "items": items,
        "createdAt": created_at.isoformat(),
        "previewUrl": f"/api/procurement/purchase-orders/{db_po.id}",
    }

# anything
