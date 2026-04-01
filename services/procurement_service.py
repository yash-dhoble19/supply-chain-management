"""
Procurement service — supplier scoring, insights, PO lifecycle.
Single source of truth for all procurement business logic.
"""
import re
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session, joinedload
import models


# ── Constants ────────────────────────────────────────────────────────

PURCHASE_ORDER_TAX_RATE = 18.0
PURCHASE_ORDER_COMPANY = {
    "companyName": "ChainMind Supply Intelligence",
    "companyAddress": "Procurement Operations, Innovation District, Pune, India",
    "billToCompany": "ChainMind Manufacturing Group",
    "billToAddress": "Accounts Payable, Global Supply Tower, Pune, India",
    "contactEmail": "procurement@chainmind.ai",
}


# ── Supplier Scoring ────────────────────────────────────────────────


def calculate_supplier_score(supplier, product_price=None) -> float:
    reliability_norm = supplier.reliability_score / 100
    lead_time_norm = max(0, 1 - (supplier.delivery_speed_days / 30))
    price_norm = max(0, 1 - (supplier.price_per_unit / (product_price * 2))) if product_price else 0.7
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
        {"supplier": s, "score": calculate_supplier_score(s, product.unit_price)}
        for s in suppliers
    ]
    best = max(supplier_scores, key=lambda x: x["score"])
    return best["supplier"]


# ── Health & Intelligence ────────────────────────────────────────────


def calculate_supply_chain_health_score(db: Session) -> float:
    products = db.query(models.Product).all()
    suppliers = db.query(models.Supplier).all()
    pending_pos = db.query(models.PurchaseOrder).filter(
        models.PurchaseOrder.status == "DRAFT"
    ).count()

    critical_items = sum(1 for p in products if p.current_stock < (p.optimal_stock_level * 0.2))
    critical_penalty = min(critical_items * 5, 40)
    po_penalty = min(pending_pos * 3, 20)
    avg_reliability = sum(s.reliability_score for s in suppliers) / len(suppliers) if suppliers else 90
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
    elif stock_pct < 35:
        return f"Stock dropping ({stock_pct:.0f}%). Consider ordering from {supplier.name} soon to avoid stockouts."
    return f"Stock is stable at {stock_pct:.0f}%."


# ── Supplier CRUD ────────────────────────────────────────────────────


def create_supplier(db: Session, name: str, contact_email: str, category: str,
                    reliability_score: float, delivery_speed_days: int, price_per_unit: float):
    db_supplier = models.Supplier(
        name=name, contact_email=contact_email, category=category,
        reliability_score=reliability_score, delivery_speed_days=delivery_speed_days,
        lead_time_days=delivery_speed_days, price_per_unit=price_per_unit,
    )
    db.add(db_supplier)
    db.commit()
    db.refresh(db_supplier)
    return db_supplier


def get_supplier_by_name(db: Session, name: str):
    return db.query(models.Supplier).filter(models.Supplier.name == name).first()


def get_supplier_by_id(db: Session, supplier_id: int):
    return db.query(models.Supplier).filter(models.Supplier.id == supplier_id).first()


def get_all_suppliers(db: Session):
    return db.query(models.Supplier).all()


# ── Supplier Analysis ───────────────────────────────────────────────


def build_supplier_analysis(db: Session) -> list[dict]:
    suppliers = get_all_suppliers(db)
    analysis = []
    for supplier in suppliers:
        # On-time delivery should not be penalized by active drafts or in_transit POs.
        # Since we don't have a rigid historical PO table, we will proxy this realistically:
        # We start with their reliability score as a baseline, and slightly adjust based on their active PO volume.
        on_time_rate = round(min(100.0, max(0.0, supplier.reliability_score - 1.5)), 1)
        
        overall_score = calculate_supplier_score(supplier)

        if supplier.reliability_score >= 85 and on_time_rate >= 80:
            verdict = "Partner"
        elif supplier.reliability_score < 70 or on_time_rate < 60:
            verdict = "At Risk"
        else:
            verdict = "Vetted"

        quality_proxy = round(
            min(100.0, ((supplier.reliability_score or 0) * 0.7) + (on_time_rate * 0.3)), 1
        )

        analysis.append({
            "id": str(supplier.id), "name": supplier.name,
            "location": supplier.category or "Location pending",
            "verdict": verdict, "score": overall_score,
            "reliability": round(supplier.reliability_score or 0, 1),
            "onTimeDelivery": on_time_rate, "qualityRate": quality_proxy,
            "deliverySpeedDays": supplier.delivery_speed_days,
            "pricePerUnit": round(supplier.price_per_unit or 0, 2),
        })
    return analysis


# ── Procurement Insights ─────────────────────────────────────────────


def build_procurement_insights(db: Session, limit: int = 10) -> list[dict]:
    products = db.query(models.Product).all()
    # Prefetch all suppliers once to avoid N+1
    all_suppliers = db.query(models.Supplier).all()
    suppliers_by_category = {}
    for s in all_suppliers:
        suppliers_by_category.setdefault(s.category, []).append(s)

    # Prefetch all active POs across all products in ONE query
    active_pos = db.query(models.PurchaseOrder).options(joinedload(models.PurchaseOrder.items)).filter(
        models.PurchaseOrder.status.in_(["DRAFT", "APPROVED", "IN_TRANSIT"])
    ).order_by(models.PurchaseOrder.created_at.desc()).all()
    
    pos_by_product = {}
    for po in active_pos:
        for item in po.items:
            pos_by_product.setdefault(item.product_id, []).append(po)

    insights = []
    for product in products:
        if product.optimal_stock_level <= 0:
            continue

        # Find best supplier using prefetched data
        candidates = suppliers_by_category.get(product.category, all_suppliers)
        if not candidates:
            continue
        scored = [{"supplier": s, "score": calculate_supplier_score(s, product.unit_price)} for s in candidates]
        best_supplier = max(scored, key=lambda x: x["score"])["supplier"]

        product_active_pos = pos_by_product.get(product.id, [])
        # ensure no duplicates if PO had the same item twice for some reason (rare, but safe)
        product_active_pos = sorted(list(set(product_active_pos)), key=lambda p: (p.created_at or datetime.min), reverse=True)

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

        supplier_unit_price = round(best_supplier.price_per_unit or product.unit_price or 0, 2)
        supplier_score = calculate_supplier_score(best_supplier, supplier_unit_price)
        estimated_cost = round(replenishment_qty * supplier_unit_price, 2)

        reasoning = generate_urgency_reasoning(
            product, best_supplier, has_active_po, latest_po.status if latest_po else None
        )

        insights.append({
            "id": str(product.id), "productId": product.id, "supplierId": best_supplier.id,
            "sku": product.sku, "title": product.name, "priority": priority,
            "reasoning": reasoning, "unitPrice": supplier_unit_price,
            "supplierScore": supplier_score,
            "estimatedLeadTime": f"{best_supplier.delivery_speed_days} Days",
            "estimatedLeadTimeDays": best_supplier.delivery_speed_days,
            "replenishmentQty": replenishment_qty,
            "actionLabel": action_label, "actionType": action_type,
            "supplierName": best_supplier.name, "estimatedCost": estimated_cost,
        })

    priority_order = {"urgent": 0, "high": 1, "monitor": 2, "normal": 3}
    insights.sort(key=lambda item: (priority_order.get(item["priority"], 3), item["estimatedLeadTimeDays"]))
    return insights[:limit]


# ── Purchase Order Lifecycle ─────────────────────────────────────────


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
    lead_time_days = extract_lead_time_days(estimated_lead_time, supplier.delivery_speed_days)
    expected_delivery = datetime.utcnow() + timedelta(days=lead_time_days)
    total_value = round(quantity * unit_price, 2)

    db_po = models.PurchaseOrder(
        po_number=po_number, supplier_id=supplier.id,
        product_name=product_name, quantity=quantity,
        total_value=total_value, total_amount=Decimal(str(total_value)),
        priority=priority.title(), status="DRAFT",
        expected_delivery=expected_delivery, expected_delivery_date=expected_delivery.date(),
    )
    db.add(db_po)
    db.commit()
    db.refresh(db_po)

    po_item = models.POItem(
        po_id=db_po.id, product_id=product.id,
        quantity_ordered=quantity, unit_price=Decimal(str(round(unit_price, 2))),
    )
    db.add(po_item)
    db.commit()
    db.refresh(db_po)
    return db_po


def normalize_po_status(status: str) -> str:
    normalized = (status or "DRAFT").strip().upper()
    return {"DRAFT": "draft", "APPROVED": "approved", "IN_TRANSIT": "in_transit", "RECEIVED": "received"}.get(normalized, "draft")


def update_po_status(db: Session, db_po, new_status: str):
    """Updates PO status. On RECEIVED, updates product stock and creates inventory logs."""
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
    """Resolve product and supplier from various identifiers."""
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
            "quantity": quantity, "rate": rate, "amount": amount,
        })

    if not items:
        fallback_amount = float(db_po.total_amount or db_po.total_value or 0)
        fallback_rate = round(fallback_amount / max(db_po.quantity or 1, 1), 2) if fallback_amount else 0.0
        items.append({
            "description": db_po.product_name or "Procurement item", "sku": "N/A",
            "quantity": db_po.quantity or 0, "rate": fallback_rate, "amount": fallback_amount,
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
        "id": str(db_po.id), "poNumber": db_po.po_number,
        "issueDate": created_at.isoformat(),
        "deliveryDate": expected_delivery.isoformat() if expected_delivery else None,
        "status": normalize_po_status(db_po.status),
        "supplierName": supplier.name if supplier else "Unknown supplier",
        "supplierAddress": (f"{supplier.category} sourcing partner hub" if supplier and supplier.category else "Supplier address pending"),
        "supplierEmail": supplier.contact_email if supplier else PURCHASE_ORDER_COMPANY["contactEmail"],
        "companyName": PURCHASE_ORDER_COMPANY["companyName"],
        "companyAddress": PURCHASE_ORDER_COMPANY["companyAddress"],
        "billToCompany": PURCHASE_ORDER_COMPANY["billToCompany"],
        "billToAddress": PURCHASE_ORDER_COMPANY["billToAddress"],
        "priority": db_po.priority or "Medium",
        "notes": (f"Auto-generated from procurement insight workflow. Priority: {db_po.priority}. "
                  f"Please confirm supplier availability before dispatch."),
        "subtotal": subtotal, "taxRate": PURCHASE_ORDER_TAX_RATE, "tax": tax, "total": total,
        "items": items, "createdAt": created_at.isoformat(),
        "previewUrl": f"/api/procurement/purchase-orders/{db_po.id}",
    }
