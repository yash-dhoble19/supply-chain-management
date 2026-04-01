"""
Dashboard service — aggregation logic for the executive dashboard.
"""
from datetime import datetime

from sqlalchemy import case, func
from sqlalchemy.orm import Session, joinedload, load_only

import models
from services.product_service import get_inventory_metrics


DASHBOARD_SHIPMENT_FIELDS = (
    models.Shipment.id,
    models.Shipment.tracking_number,
    models.Shipment.origin,
    models.Shipment.destination,
    models.Shipment.status,
    models.Shipment.progress_percent,
    models.Shipment.eta,
    models.Shipment.created_at,
)


def _shipment_status_tone(status: str) -> str:
    return {"IN_TRANSIT": "primary", "SCHEDULED": "neutral", "DELAYED": "warning", "DELIVERED": "success"}.get(
        status, "neutral"
    )


def _activity_timestamp(value) -> str:
    if not value:
        return datetime.utcnow().isoformat()
    return value.isoformat()


def _normalize_status(value: str | None, fallback: str) -> str:
    return (value or fallback).replace("_", " ").title()


def _count_statuses(query, column, fallback: str) -> dict[str, int]:
    return {
        _normalize_status(status, fallback): int(count)
        for status, count in query.group_by(column).all()
    }


def get_dashboard_metrics(db: Session) -> list[dict]:
    metrics_data = get_inventory_metrics(db)
    total_value = metrics_data.get("total_value", 0.0)

    product_summary = db.query(
        func.count(models.Product.id).label("total_skus"),
        func.count(func.distinct(models.Product.category)).label("categories"),
        func.coalesce(
            func.sum(
                case(
                    (models.Product.current_stock < models.Product.safety_stock_level, 1),
                    else_=0,
                )
            ),
            0,
        ).label("critical_stock"),
        func.coalesce(
            func.sum(
                case(
                    (
                        (models.Product.current_stock >= models.Product.safety_stock_level)
                        & (models.Product.current_stock < (models.Product.safety_stock_level * 1.2)),
                        1,
                    ),
                    else_=0,
                )
            ),
            0,
        ).label("low_stock"),
    ).one()

    purchase_order_summary = db.query(
        func.coalesce(
            func.sum(case((models.PurchaseOrder.status != "RECEIVED", 1), else_=0)),
            0,
        ).label("active_pos"),
        func.coalesce(
            func.sum(case((models.PurchaseOrder.status == "IN_TRANSIT", 1), else_=0)),
            0,
        ).label("in_transit_pos"),
    ).one()

    total_skus = int(product_summary.total_skus or 0)
    categories = int(product_summary.categories or 0)
    critical_stock = int(product_summary.critical_stock or 0)
    low_stock = int(product_summary.low_stock or 0)
    active_pos = int(purchase_order_summary.active_pos or 0)
    in_transit_pos = int(purchase_order_summary.in_transit_pos or 0)

    return [
        {
            "id": "total-skus",
            "title": "Total SKUs",
            "value": total_skus,
            "status": "Catalog coverage",
            "change": f"{categories} active categories",
            "tone": "primary",
            "icon": "inventory_2",
            "format": "number",
        },
        {
            "id": "critical-stock",
            "title": "Critical Stock",
            "value": critical_stock,
            "status": "Action required" if critical_stock else "Stable",
            "change": f"{total_skus and round((critical_stock / total_skus) * 100) or 0}% of catalog",
            "tone": "danger" if critical_stock else "success",
            "icon": "warning",
            "format": "number",
        },
        {
            "id": "low-stock",
            "title": "Low Stock",
            "value": low_stock,
            "status": "Needs review" if low_stock else "Healthy",
            "change": "Monitor replenishment pipeline",
            "tone": "warning" if low_stock else "success",
            "icon": "schedule",
            "format": "number",
        },
        {
            "id": "active-pos",
            "title": "Active POs",
            "value": active_pos,
            "status": "Procurement active" if active_pos else "No open orders",
            "change": f"{in_transit_pos} in transit",
            "tone": "neutral",
            "icon": "sync",
            "format": "number",
        },
        {
            "id": "inventory-value",
            "title": "Inventory Value",
            "value": total_value,
            "status": "Tracked inventory",
            "change": f"{total_skus} items valued live",
            "tone": "success",
            "icon": "payments",
            "format": "currency",
        },
    ]


def get_dashboard_shipments(db: Session) -> list[dict]:
    shipments = (
        db.query(models.Shipment)
        .options(load_only(*DASHBOARD_SHIPMENT_FIELDS))
        .order_by(models.Shipment.created_at.desc())
        .limit(12)
        .all()
    )
    results = []
    for shipment in shipments:
        status = shipment.status or "SCHEDULED"
        status_label = status.replace("_", " ").title()
        progress = round(shipment.progress_percent or 0)
        detail = {
            "DELAYED": "Requires attention from logistics team",
            "DELIVERED": "Completed and closed",
            "IN_TRANSIT": "Carrier en route",
        }.get(status, "Awaiting dispatch")
        results.append(
            {
                "id": str(shipment.id),
                "trackingNumber": shipment.tracking_number,
                "source": shipment.origin,
                "destination": shipment.destination,
                "status": status_label,
                "progress": progress,
                "eta": shipment.eta.isoformat() if shipment.eta else None,
                "detail": detail,
                "tone": _shipment_status_tone(status),
            }
        )
    return results


def get_dashboard_activities(db: Session, limit: int = 8) -> list[dict]:
    activities = []

    logs = (
        db.query(models.InventoryLog)
        .options(joinedload(models.InventoryLog.product))
        .order_by(models.InventoryLog.change_date.desc())
        .limit(limit)
        .all()
    )
    for log in logs:
        product = log.product
        product_name = product.name if product else f"Product #{log.product_id}"
        qty = abs(log.quantity_change or 0)
        action = "added" if (log.quantity_change or 0) >= 0 else "removed"
        reason = (log.reason or "stock update").replace("_", " ").title()
        activities.append(
            {
                "id": f"inventory-{log.id}",
                "title": f"{product_name} stock updated",
                "description": f"{qty} units {action} via {reason}",
                "timestamp": _activity_timestamp(log.change_date),
                "type": "inventory",
            }
        )

    purchase_orders = (
        db.query(models.PurchaseOrder)
        .options(joinedload(models.PurchaseOrder.supplier))
        .order_by(models.PurchaseOrder.created_at.desc())
        .limit(limit)
        .all()
    )
    for purchase_order in purchase_orders:
        supplier_name = purchase_order.supplier.name if purchase_order.supplier else "Unknown supplier"
        status_label = (purchase_order.status or "DRAFT").replace("_", " ").title()
        activities.append(
            {
                "id": f"po-{purchase_order.id}",
                "title": f"PO {purchase_order.po_number} {status_label.lower()}",
                "description": f"{purchase_order.quantity or 0} units of {purchase_order.product_name or 'inventory'} with {supplier_name}",
                "timestamp": _activity_timestamp(purchase_order.created_at),
                "type": "procurement",
            }
        )

    shipments = (
        db.query(models.Shipment)
        .options(load_only(*DASHBOARD_SHIPMENT_FIELDS))
        .order_by(models.Shipment.created_at.desc())
        .limit(limit)
        .all()
    )
    for shipment in shipments:
        status_label = (shipment.status or "SCHEDULED").replace("_", " ").title()
        activities.append(
            {
                "id": f"shipment-{shipment.id}",
                "title": f"Shipment {shipment.tracking_number} {status_label.lower()}",
                "description": f"{shipment.origin} to {shipment.destination} at {round(shipment.progress_percent or 0)}% completion",
                "timestamp": _activity_timestamp(shipment.created_at),
                "type": "shipment",
            }
        )

    orders = db.query(models.Order).order_by(models.Order.created_at.desc()).limit(limit).all()
    for order in orders:
        status_label = (order.status or "PENDING").replace("_", " ").title()
        activities.append(
            {
                "id": f"order-{order.id}",
                "title": f"Order #{order.id} {status_label.lower()}",
                "description": f"{order.customer_name} delivery to {order.delivery_address or 'address pending'}",
                "timestamp": _activity_timestamp(order.created_at),
                "type": "order",
            }
        )

    activities.sort(key=lambda item: item["timestamp"], reverse=True)
    return activities[:limit]


def get_dashboard_stats(db: Session) -> list[dict]:
    raw_material_summary = db.query(
        func.count(models.Product.id).label("sku_count"),
        func.coalesce(func.sum(models.Product.current_stock), 0).label("raw_material_units"),
    ).filter(func.lower(models.Product.stage) == "raw material").one()

    active_shipment_summary = db.query(
        func.count(models.Shipment.id).label("active_shipments"),
        func.coalesce(func.avg(models.Shipment.progress_percent), 0.0).label("avg_progress"),
    ).filter(models.Shipment.status.in_(["SCHEDULED", "IN_TRANSIT", "DELAYED"])).one()

    active_carriers = db.query(models.Shipment.carrier_id).filter(
        models.Shipment.carrier_id.isnot(None)
    ).distinct().count()
    total_carriers = db.query(models.Carrier).count()

    raw_material_units = int(raw_material_summary.raw_material_units or 0)
    raw_material_skus = int(raw_material_summary.sku_count or 0)
    active_shipments = int(active_shipment_summary.active_shipments or 0)
    avg_progress = round(float(active_shipment_summary.avg_progress or 0.0), 1)

    return [
        {
            "id": "raw-material",
            "label": "Raw Material Stock",
            "value": f"{raw_material_units:,} units",
            "description": f"{raw_material_skus} raw material SKUs",
            "icon": "inventory",
        },
        {
            "id": "delivery-progress",
            "label": "Avg. Delivery Progress",
            "value": f"{avg_progress}%",
            "description": f"{active_shipments} active routes",
            "icon": "local_shipping",
        },
        {
            "id": "active-carriers",
            "label": "Active Carriers",
            "value": f"{active_carriers} / {total_carriers}",
            "description": "Assigned to live shipments",
            "icon": "factory",
        },
    ]


def get_dashboard_overview(db: Session) -> dict:
    inventory_status_expr = case(
        (models.Product.current_stock < models.Product.safety_stock_level, "Critical"),
        (models.Product.current_stock < (models.Product.safety_stock_level * 1.2), "Low"),
        else_="Healthy",
    )
    inventory_stage_expr = func.coalesce(models.Product.stage, "Unknown")
    shipment_status_expr = func.coalesce(models.Shipment.status, "SCHEDULED")
    order_status_expr = func.coalesce(models.Order.status, "PENDING")
    purchase_order_status_expr = func.coalesce(models.PurchaseOrder.status, "DRAFT")

    inventory_status_rows = (
        db.query(inventory_status_expr.label("status"), func.count(models.Product.id))
        .group_by(inventory_status_expr)
        .all()
    )
    inventory_stage_rows = (
        db.query(inventory_stage_expr.label("stage"), func.count(models.Product.id))
        .group_by(inventory_stage_expr)
        .all()
    )
    shipment_counts = _count_statuses(
        db.query(shipment_status_expr.label("status"), func.count(models.Shipment.id)),
        shipment_status_expr,
        "SCHEDULED",
    )
    order_counts = _count_statuses(
        db.query(order_status_expr.label("status"), func.count(models.Order.id)),
        order_status_expr,
        "PENDING",
    )
    purchase_order_counts = _count_statuses(
        db.query(purchase_order_status_expr.label("status"), func.count(models.PurchaseOrder.id)),
        purchase_order_status_expr,
        "DRAFT",
    )

    inventory_counts = {"Healthy": 0, "Low": 0, "Critical": 0}
    for status, count in inventory_status_rows:
        inventory_counts[status] = int(count)

    top_inventory_rows = (
        db.query(
            models.Product.id,
            models.Product.name,
            models.Product.sku,
            models.Product.category,
            models.Product.current_stock,
            inventory_status_expr.label("status"),
            (func.coalesce(models.Product.current_stock, 0) * func.coalesce(models.Product.unit_price, 0)).label("value"),
        )
        .order_by((func.coalesce(models.Product.current_stock, 0) * func.coalesce(models.Product.unit_price, 0)).desc())
        .limit(5)
        .all()
    )
    top_inventory = [
        {
            "id": str(row.id),
            "name": row.name,
            "sku": row.sku,
            "category": row.category,
            "value": round(float(row.value or 0.0), 2),
            "stock": row.current_stock or 0,
            "status": row.status,
        }
        for row in top_inventory_rows
    ]

    delayed_shipments = int(
        db.query(func.count(models.Shipment.id))
        .filter(func.coalesce(models.Shipment.status, "SCHEDULED") == "DELAYED")
        .scalar()
        or 0
    )
    pending_orders = int(
        db.query(func.count(models.Order.id))
        .filter(func.coalesce(models.Order.status, "PENDING") == "PENDING")
        .scalar()
        or 0
    )
    critical_products = inventory_counts["Critical"]

    def _to_series(counts, default_tone="neutral"):
        return [
            {"id": label.lower().replace(" ", "-"), "label": label, "value": value, "tone": default_tone}
            for label, value in sorted(counts.items(), key=lambda item: item[1], reverse=True)
        ]

    return {
        "inventoryStatus": [
            {"id": "healthy", "label": "Healthy", "value": inventory_counts["Healthy"], "tone": "success"},
            {"id": "low", "label": "Low", "value": inventory_counts["Low"], "tone": "warning"},
            {"id": "critical", "label": "Critical", "value": inventory_counts["Critical"], "tone": "danger"},
        ],
        "inventoryStages": [
            {
                "id": str(stage).lower().replace(" ", "-"),
                "label": str(stage),
                "value": int(count),
                "tone": "primary",
            }
            for stage, count in sorted(inventory_stage_rows, key=lambda item: item[1], reverse=True)
        ],
        "shipmentStatus": _to_series(shipment_counts),
        "orderStatus": _to_series(order_counts),
        "purchaseOrderStatus": _to_series(purchase_order_counts),
        "topInventory": top_inventory,
        "executiveBriefs": [
            {
                "id": "critical-stock",
                "title": "Critical replenishment pressure",
                "description": f"{critical_products} SKUs are below safety stock and need procurement attention.",
                "tone": "danger" if critical_products else "success",
            },
            {
                "id": "shipment-risk",
                "title": "Logistics watchlist",
                "description": f"{delayed_shipments} shipments are currently delayed across the network.",
                "tone": "warning" if delayed_shipments else "success",
            },
            {
                "id": "order-backlog",
                "title": "Demand backlog",
                "description": f"{pending_orders} customer orders remain pending fulfillment.",
                "tone": "neutral" if pending_orders else "success",
            },
        ],
    }
