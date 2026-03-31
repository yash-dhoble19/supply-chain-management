"""
Dashboard service — aggregation logic for the executive dashboard.
"""
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session
import models
from services.product_service import get_inventory_status, get_inventory_metrics


def get_dashboard_metrics(db: Session) -> list[dict]:
    # must be loaded from DB using explicit SUM operations
    metrics_data = get_inventory_metrics(db)
    total_items = metrics_data.get("total_items", 0)
    total_value = metrics_data.get("total_value", 0.0)

    products = db.query(models.Product).all()
    purchase_orders = db.query(models.PurchaseOrder).all()

    total_skus = len(products)
    categories = len({p.category for p in products if p.category})
    critical_stock = sum(1 for p in products if (p.current_stock or 0) < (p.safety_stock_level or 0))
    low_stock = sum(
        1 for p in products
        if (p.current_stock or 0) >= (p.safety_stock_level or 0)
        and (p.current_stock or 0) < ((p.safety_stock_level or 0) * 1.2)
    )
    active_pos = sum(1 for po in purchase_orders if po.status != "RECEIVED")
    in_transit_pos = sum(1 for po in purchase_orders if po.status == "IN_TRANSIT")
    inventory_value = total_value

    return [
        {"id": "total-skus", "title": "Total SKUs", "value": total_skus, "status": "Catalog coverage",
         "change": f"{categories} active categories", "tone": "primary", "icon": "inventory_2", "format": "number"},
        {"id": "critical-stock", "title": "Critical Stock", "value": critical_stock,
         "status": "Action required" if critical_stock else "Stable",
         "change": f"{total_skus and round((critical_stock / total_skus) * 100) or 0}% of catalog",
         "tone": "danger" if critical_stock else "success", "icon": "warning", "format": "number"},
        {"id": "low-stock", "title": "Low Stock", "value": low_stock,
         "status": "Needs review" if low_stock else "Healthy",
         "change": "Monitor replenishment pipeline",
         "tone": "warning" if low_stock else "success", "icon": "schedule", "format": "number"},
        {"id": "active-pos", "title": "Active POs", "value": active_pos,
         "status": "Procurement active" if active_pos else "No open orders",
         "change": f"{in_transit_pos} in transit", "tone": "neutral", "icon": "sync", "format": "number"},
        {"id": "inventory-value", "title": "Inventory Value", "value": inventory_value,
         "status": "Tracked inventory", "change": f"{total_skus} items valued live",
         "tone": "success", "icon": "payments", "format": "currency"},
    ]


def _shipment_status_tone(status: str) -> str:
    return {"IN_TRANSIT": "primary", "SCHEDULED": "neutral", "DELAYED": "warning", "DELIVERED": "success"}.get(status, "neutral")


def _activity_timestamp(value) -> str:
    if not value:
        return datetime.utcnow().isoformat()
    return value.isoformat()


def get_dashboard_shipments(db: Session) -> list[dict]:
    shipments = db.query(models.Shipment).order_by(models.Shipment.created_at.desc()).limit(12).all()
    results = []
    for s in shipments:
        status = s.status or "SCHEDULED"
        status_label = status.replace("_", " ").title()
        progress = round(s.progress_percent or 0)
        detail = {"DELAYED": "Requires attention from logistics team", "DELIVERED": "Completed and closed",
                  "IN_TRANSIT": "Carrier en route"}.get(status, "Awaiting dispatch")
        results.append({
            "id": str(s.id), "trackingNumber": s.tracking_number, "source": s.origin,
            "destination": s.destination, "status": status_label, "progress": progress,
            "eta": s.eta.isoformat() if s.eta else None, "detail": detail,
            "tone": _shipment_status_tone(status),
        })
    return results


def get_dashboard_activities(db: Session, limit: int = 8) -> list[dict]:
    activities = []

    product_lookup = {p.id: p for p in db.query(models.Product).all()}

    logs = db.query(models.InventoryLog).order_by(models.InventoryLog.change_date.desc()).limit(limit).all()
    for log in logs:
        product = product_lookup.get(log.product_id)
        product_name = product.name if product else f"Product #{log.product_id}"
        qty = abs(log.quantity_change or 0)
        action = "added" if (log.quantity_change or 0) >= 0 else "removed"
        reason = (log.reason or "stock update").replace("_", " ").title()
        activities.append({
            "id": f"inventory-{log.id}", "title": f"{product_name} stock updated",
            "description": f"{qty} units {action} via {reason}",
            "timestamp": _activity_timestamp(log.change_date), "type": "inventory",
        })

    from sqlalchemy.orm import joinedload
    pos = db.query(models.PurchaseOrder).options(joinedload(models.PurchaseOrder.supplier)).order_by(models.PurchaseOrder.created_at.desc()).limit(limit).all()
    for po in pos:
        supplier_name = po.supplier.name if po.supplier else "Unknown supplier"
        status_label = (po.status or "DRAFT").replace("_", " ").title()
        activities.append({
            "id": f"po-{po.id}", "title": f"PO {po.po_number} {status_label.lower()}",
            "description": f"{po.quantity or 0} units of {po.product_name or 'inventory'} with {supplier_name}",
            "timestamp": _activity_timestamp(po.created_at), "type": "procurement",
        })

    shipments = db.query(models.Shipment).order_by(models.Shipment.created_at.desc()).limit(limit).all()
    for s in shipments:
        status_label = (s.status or "SCHEDULED").replace("_", " ").title()
        activities.append({
            "id": f"shipment-{s.id}", "title": f"Shipment {s.tracking_number} {status_label.lower()}",
            "description": f"{s.origin} to {s.destination} at {round(s.progress_percent or 0)}% completion",
            "timestamp": _activity_timestamp(s.created_at), "type": "shipment",
        })

    orders = db.query(models.Order).order_by(models.Order.created_at.desc()).limit(limit).all()
    for order in orders:
        status_label = (order.status or "PENDING").replace("_", " ").title()
        activities.append({
            "id": f"order-{order.id}", "title": f"Order #{order.id} {status_label.lower()}",
            "description": f"{order.customer_name} delivery to {order.delivery_address or 'address pending'}",
            "timestamp": _activity_timestamp(order.created_at), "type": "order",
        })

    activities.sort(key=lambda item: item["timestamp"], reverse=True)
    return activities[:limit]


def get_dashboard_stats(db: Session) -> list[dict]:
    raw_material_products = db.query(models.Product).filter(func.lower(models.Product.stage) == "raw material").all()
    raw_material_units = sum(p.current_stock or 0 for p in raw_material_products)

    active_shipments = db.query(models.Shipment).filter(
        models.Shipment.status.in_(["SCHEDULED", "IN_TRANSIT", "DELAYED"])
    ).all()
    avg_progress = round(
        sum(s.progress_percent or 0 for s in active_shipments) / len(active_shipments), 1
    ) if active_shipments else 0.0

    active_carriers = db.query(models.Shipment.carrier_id).filter(
        models.Shipment.carrier_id.isnot(None)
    ).distinct().count()
    total_carriers = db.query(models.Carrier).count()

    return [
        {"id": "raw-material", "label": "Raw Material Stock", "value": f"{raw_material_units:,} units",
         "description": f"{len(raw_material_products)} raw material SKUs", "icon": "inventory"},
        {"id": "delivery-progress", "label": "Avg. Delivery Progress", "value": f"{avg_progress}%",
         "description": f"{len(active_shipments)} active routes", "icon": "local_shipping"},
        {"id": "active-carriers", "label": "Active Carriers", "value": f"{active_carriers} / {total_carriers}",
         "description": "Assigned to live shipments", "icon": "factory"},
    ]


def get_dashboard_overview(db: Session) -> dict:
    products = db.query(models.Product).all()
    shipments = db.query(models.Shipment).all()
    orders = db.query(models.Order).all()
    purchase_orders = db.query(models.PurchaseOrder).all()

    inv_counts = {"Healthy": 0, "Low": 0, "Critical": 0}
    inv_stages = {}
    product_value_rows = []

    for p in products:
        if (p.current_stock or 0) < (p.safety_stock_level or 0):
            status = "Critical"
        elif (p.current_stock or 0) < ((p.safety_stock_level or 0) * 1.2):
            status = "Low"
        else:
            status = "Healthy"
            
        inv_counts[status] += 1
        stage = p.stage or "Unknown"
        inv_stages[stage] = inv_stages.get(stage, 0) + 1
        inv_value = round((p.current_stock or 0) * (p.unit_price or 0), 2)
        product_value_rows.append({
            "id": str(p.id), "name": p.name, "sku": p.sku,
            "category": p.category, "value": inv_value,
            "stock": p.current_stock or 0, "status": status,
        })

    def _count_statuses(items, default_status):
        counts = {}
        for item in items:
            s = (getattr(item, "status", None) or default_status).replace("_", " ").title()
            counts[s] = counts.get(s, 0) + 1
        return counts

    shipment_counts = _count_statuses(shipments, "SCHEDULED")
    order_counts = _count_statuses(orders, "PENDING")
    po_counts = _count_statuses(purchase_orders, "DRAFT")

    top_inventory = sorted(product_value_rows, key=lambda x: x["value"], reverse=True)[:5]
    critical_products = [r for r in product_value_rows if r["status"] == "Critical"]
    delayed_shipments = [s for s in shipments if (s.status or "").upper() == "DELAYED"]
    pending_orders = [o for o in orders if (o.status or "").upper() == "PENDING"]

    def _to_series(counts, default_tone="neutral"):
        return [
            {"id": label.lower().replace(" ", "-"), "label": label, "value": value, "tone": default_tone}
            for label, value in sorted(counts.items(), key=lambda x: x[1], reverse=True)
        ]

    return {
        "inventoryStatus": [
            {"id": "healthy", "label": "Healthy", "value": inv_counts["Healthy"], "tone": "success"},
            {"id": "low", "label": "Low", "value": inv_counts["Low"], "tone": "warning"},
            {"id": "critical", "label": "Critical", "value": inv_counts["Critical"], "tone": "danger"},
        ],
        "inventoryStages": [
            {"id": s.lower().replace(" ", "-"), "label": s, "value": c, "tone": "primary"}
            for s, c in sorted(inv_stages.items(), key=lambda x: x[1], reverse=True)
        ],
        "shipmentStatus": _to_series(shipment_counts),
        "orderStatus": _to_series(order_counts),
        "purchaseOrderStatus": _to_series(po_counts),
        "topInventory": top_inventory,
        "executiveBriefs": [
            {"id": "critical-stock", "title": "Critical replenishment pressure",
             "description": f"{len(critical_products)} SKUs are below safety stock and need procurement attention.",
             "tone": "danger" if critical_products else "success"},
            {"id": "shipment-risk", "title": "Logistics watchlist",
             "description": f"{len(delayed_shipments)} shipments are currently delayed across the network.",
             "tone": "warning" if delayed_shipments else "success"},
            {"id": "order-backlog", "title": "Demand backlog",
             "description": f"{len(pending_orders)} customer orders remain pending fulfillment.",
             "tone": "neutral" if pending_orders else "success"},
        ],
    }
