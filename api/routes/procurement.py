"""
Procurement routes - /api/procurement/*
Consolidated supplier management lives on the procurement router and uses the
suppliers table as the single source of truth.
"""
from datetime import datetime
from math import ceil
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

import database
import models
from schemas.procurement import POStatusUpdate, ProcurementRequest, QuickPOCreate, SupplierWrite
from services import ai_service, procurement_service
from services.pdf_service import build_purchase_order_pdf


router = APIRouter(tags=["Procurement"])


def _build_supplier_overview_response(analysis: list[dict]) -> dict:
    avg_reliability = round(sum(item["reliability"] for item in analysis) / len(analysis), 1) if analysis else 0.0
    on_time_delivery = round(sum(item["onTimeDelivery"] for item in analysis) / len(analysis), 1) if analysis else 0.0
    quality_rate = round(sum(item["qualityRate"] for item in analysis) / len(analysis), 1) if analysis else 0.0
    average_score = round(sum(item["score"] for item in analysis) / len(analysis), 1) if analysis else 0.0
    esg = "A+" if average_score >= 95 else "A" if average_score >= 90 else "B+" if average_score >= 80 else "B"
    return {
        "overview": {
            "avgReliability": avg_reliability,
            "onTimeDelivery": on_time_delivery,
            "qualityRate": quality_rate,
            "esgCompliance": esg,
        },
        "suppliers": analysis,
    }


def _build_top_performers_from_analysis(analysis: list[dict]) -> list[dict]:
    performers = []
    for idx, supplier in enumerate(sorted(analysis, key=lambda item: item["score"], reverse=True)[:3], start=1):
        metric = (
            f"{supplier['qualityRate']}% Quality"
            if idx == 1
            else f"{supplier['onTimeDelivery']}% On-time"
            if idx == 2
            else f"{supplier['reliability']}% Reliability"
        )
        performers.append(
            {
                "id": supplier["id"],
                "rank": idx,
                "name": supplier["name"],
                "metricLabel": metric,
                "score": supplier["score"],
            }
        )
    return performers


def _build_spend_optimization_response(db: Session, insights: list[dict]) -> dict:
    product_lookup = {product.id: product for product in db.query(models.Product).all()}
    baseline_spend = sum(
        insight["replenishmentQty"] * (product_lookup.get(insight["productId"], models.Product()).unit_price or 0)
        for insight in insights
    )
    optimized_spend = sum(insight["estimatedCost"] for insight in insights)
    total_value = round(max(0, baseline_spend - optimized_spend), 2)
    budget_pool = optimized_spend + max(total_value * 4, optimized_spend * 0.2, 1)
    budget_utilization = round((optimized_spend / budget_pool) * 100, 1) if budget_pool else 0.0
    return {
        "totalValue": total_value,
        "yoyChange": f"+{round((total_value / max(baseline_spend, 1)) * 100, 1)}% projected",
        "budgetUtilization": budget_utilization,
        "buttonLabel": "Download Report",
    }


def _build_procurement_summary(db: Session, insights: Optional[list[dict]] = None) -> dict:
    products = db.query(
        models.Product.id,
        models.Product.name,
        models.Product.current_stock,
        models.Product.optimal_stock_level,
        models.Product.unit_price,
    ).all()
    suppliers = db.query(models.Supplier).all()
    pending_pos = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.status == "DRAFT").count()
    incoming_rows = (
        db.query(
            models.POItem.product_id,
            func.coalesce(func.sum(models.POItem.quantity_ordered), 0).label("incoming_qty"),
        )
        .join(models.PurchaseOrder)
        .filter(models.PurchaseOrder.status.in_(["DRAFT", "APPROVED", "IN_TRANSIT"]))
        .group_by(models.POItem.product_id)
        .all()
    )
    incoming_by_product = {row.product_id: int(row.incoming_qty or 0) for row in incoming_rows}

    critical_items = 0
    critical_names: list[str] = []
    for product in products:
        incoming_qty = incoming_by_product.get(product.id, 0)
        if (product.current_stock + incoming_qty) < (product.optimal_stock_level * 0.2):
            critical_items += 1
            if len(critical_names) < 2:
                critical_names.append(product.name)

    avg_reliability = (
        sum(procurement_service.get_supplier_reliability_percent(supplier) for supplier in suppliers) / len(suppliers)
        if suppliers else 90
    )
    health_score = max(0, min(100, 100 - min(critical_items * 5, 40) - min(pending_pos * 3, 20) + ((avg_reliability - 80) / 2)))

    summary_insights = insights if insights is not None else procurement_service.build_procurement_insights(db, limit=12)
    product_lookup = {product.id: product for product in products}
    savings_to_date = round(
        sum(
            max(0, (product_lookup[insight["productId"]].unit_price or 0) - insight["unitPrice"])
            * insight["replenishmentQty"]
            for insight in summary_insights
            if insight["productId"] in product_lookup and insight["actionType"] == "quick_po"
        ),
        2,
    )
    projected_spend = sum(insight["estimatedCost"] for insight in summary_insights if insight["actionType"] == "quick_po")
    savings_pct = round((savings_to_date / max(projected_spend, 1)) * 100, 1)

    avg_supplier_lead = (
        round(sum(procurement_service.get_supplier_average_delivery_days(supplier) for supplier in suppliers) / len(suppliers))
        if suppliers else 0
    )
    fastest_lead = min((procurement_service.get_supplier_average_delivery_days(supplier) for supplier in suppliers), default=avg_supplier_lead)
    lead_opportunity = max(avg_supplier_lead - fastest_lead, 0)
    status = "optimal" if health_score >= 80 else "warning" if health_score >= 60 else "critical"

    return {
        "systemHealthScore": round(health_score),
        "healthStatus": status,
        "aiBriefing": procurement_service.generate_morning_briefing(health_score, critical_items, pending_pos, critical_names),
        "criticalItems": critical_items,
        "pendingPOs": pending_pos,
        "savingsToDate": savings_to_date,
        "savingsChange": f"+{savings_pct}% projected",
        "leadTimeAverage": f"{avg_supplier_lead}d",
        "leadTimeChange": f"-{lead_opportunity}d opportunity" if lead_opportunity else "Stable lead time",
    }


def _matches_text(value: Optional[str], query: str) -> bool:
    return query in (value or "").lower()


def _reliability_matches(record: dict, delivery_reliability_range: Optional[str]) -> bool:
    if not delivery_reliability_range or delivery_reliability_range == "all":
        return True
    reliability = float(record["reliability_percent"])
    if delivery_reliability_range == "95-100":
        return reliability >= 95
    if delivery_reliability_range == "90-94":
        return 90 <= reliability < 95
    if delivery_reliability_range == "80-89":
        return 80 <= reliability < 90
    if delivery_reliability_range == "0-79":
        return reliability < 80
    return True


def _build_supplier_management_summary(records: list[dict]) -> dict:
    total_orders = sum(record["total_orders"] for record in records)
    total_spend = round(sum(record["total_spend"] for record in records), 2)
    avg_score = round(sum(record["supplier_score"] for record in records) / len(records), 1) if records else 0.0
    active_suppliers = sum(1 for record in records if record["raw_status"] == "ACTIVE")
    preferred_suppliers = sum(1 for record in records if record["preferred_supplier"])
    return {
        "total_suppliers": len(records),
        "active_suppliers": active_suppliers,
        "preferred_suppliers": preferred_suppliers,
        "avg_supplier_score": avg_score,
        "total_purchase_orders": total_orders,
        "total_spend": total_spend,
    }


def _build_supplier_filter_options(records: list[dict]) -> dict:
    def _distinct(key: str) -> list[str]:
        return sorted({record[key] for record in records if record.get(key)})

    return {
        "supplier_types": _distinct("supplier_type"),
        "statuses": ["Active", "Preferred", "Inactive", "Blocked", "At Risk"],
        "product_categories": _distinct("product_category"),
        "locations": _distinct("location"),
        "performance_tiers": ["Elite", "Strong", "Stable", "Watch"],
        "delivery_reliability_ranges": ["95-100", "90-94", "80-89", "0-79"],
    }


def _filter_supplier_records(
    records: list[dict],
    query: Optional[str],
    supplier_type: Optional[str],
    status: Optional[str],
    product_category: Optional[str],
    location: Optional[str],
    performance_tier: Optional[str],
    delivery_reliability_range: Optional[str],
) -> list[dict]:
    filtered = records

    if query:
        normalized_query = query.strip().lower()
        filtered = [
            record for record in filtered
            if any(
                _matches_text(str(value) if value is not None else "", normalized_query)
                for value in [
                    record["supplier_name"],
                    record["company_name"],
                    record["email"],
                    record["phone"],
                    record["product_name"],
                    record["product_category"],
                    record["location"],
                ]
            )
        ]

    if supplier_type and supplier_type.lower() != "all":
        filtered = [record for record in filtered if (record["supplier_type"] or "").lower() == supplier_type.lower()]

    if status and status.lower() != "all":
        normalized_status = status.lower()
        if normalized_status == "preferred":
            filtered = [record for record in filtered if record["preferred_supplier"]]
        else:
            filtered = [record for record in filtered if (record["status"] or "").lower() == normalized_status]

    if product_category and product_category.lower() != "all":
        filtered = [record for record in filtered if (record["product_category"] or "").lower() == product_category.lower()]

    if location and location.lower() != "all":
        filtered = [record for record in filtered if (record["location"] or "").lower() == location.lower()]

    if performance_tier and performance_tier.lower() != "all":
        filtered = [record for record in filtered if (record["performance_tier"] or "").lower() == performance_tier.lower()]

    filtered = [record for record in filtered if _reliability_matches(record, delivery_reliability_range)]
    return filtered


def _sort_supplier_records(records: list[dict], sort: Optional[str]) -> list[dict]:
    sort_key = (sort or "highest_score").lower()
    if sort_key == "most_orders":
        return sorted(records, key=lambda record: (-record["total_orders"], -record["supplier_score"]))
    if sort_key == "lowest_price":
        return sorted(records, key=lambda record: (record["unit_price"], -record["supplier_score"]))
    if sort_key == "fastest_delivery":
        return sorted(records, key=lambda record: (record["average_delivery_days"], -record["supplier_score"]))
    if sort_key == "recently_added":
        return sorted(records, key=lambda record: (record["created_at"] or "", record["supplier_id"]), reverse=True)
    return sorted(records, key=lambda record: (-record["supplier_score"], -record["total_orders"]))


@router.get("/api/procurement/summary")
def get_summary(db: Session = Depends(database.get_db)):
    return _build_procurement_summary(db)


@router.get("/api/procurement/bootstrap")
def get_procurement_bootstrap(db: Session = Depends(database.get_db)):
    insights = procurement_service.build_procurement_insights(db, limit=20)
    supplier_analysis = procurement_service.build_supplier_analysis(db)
    supplier_response = _build_supplier_overview_response(supplier_analysis)
    return {
        "summary": _build_procurement_summary(db, insights=insights[:12]),
        "insights": insights[:12],
        "supplierOverview": supplier_response["overview"],
        "supplierRows": supplier_response["suppliers"],
        "topPerformers": _build_top_performers_from_analysis(supplier_analysis),
        "spendOptimization": _build_spend_optimization_response(db, insights),
        "purchaseOrders": list_purchase_orders(limit=4, page=1, db=db),
    }


@router.get("/api/procurement/insights")
def get_insights(priority: Optional[str] = None, db: Session = Depends(database.get_db)):
    insights = procurement_service.build_procurement_insights(db, limit=12)
    if priority and priority.lower() != "all":
        insights = [insight for insight in insights if insight["priority"] == priority.lower()]
    return insights


@router.get("/api/procurement/suppliers/overview")
def get_suppliers_overview(db: Session = Depends(database.get_db)):
    analysis = procurement_service.build_supplier_analysis(db)
    return _build_supplier_overview_response(analysis)


@router.get("/api/procurement/suppliers/top-performers")
def get_top_performers(db: Session = Depends(database.get_db)):
    return _build_top_performers_from_analysis(procurement_service.build_supplier_analysis(db))


@router.get("/api/procurement/spend-optimization")
def get_spend_optimization(db: Session = Depends(database.get_db)):
    return _build_spend_optimization_response(db, procurement_service.build_procurement_insights(db, limit=20))


@router.get("/api/procurement/suppliers")
def list_suppliers(
    search: Optional[str] = None,
    supplier_type: Optional[str] = None,
    status: Optional[str] = None,
    product_category: Optional[str] = None,
    location: Optional[str] = None,
    performance_tier: Optional[str] = None,
    delivery_reliability_range: Optional[str] = None,
    sort: Optional[str] = "highest_score",
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(database.get_db),
):
    records = procurement_service.build_supplier_management_records(db)
    summary = _build_supplier_management_summary(records)
    filter_options = _build_supplier_filter_options(records)
    filtered = _filter_supplier_records(
        records,
        search,
        supplier_type,
        status,
        product_category,
        location,
        performance_tier,
        delivery_reliability_range,
    )
    sorted_records = _sort_supplier_records(filtered, sort)

    safe_page_size = max(5, min(page_size, 100))
    total_items = len(sorted_records)
    total_pages = max(1, ceil(total_items / safe_page_size)) if total_items else 1
    safe_page = min(max(page, 1), total_pages)
    start = (safe_page - 1) * safe_page_size
    items = sorted_records[start:start + safe_page_size]

    return {
        "summary": summary,
        "filters": filter_options,
        "items": items,
        "pagination": {
            "page": safe_page,
            "page_size": safe_page_size,
            "total_items": total_items,
            "total_pages": total_pages,
            "filtered_items": len(filtered),
        },
    }


@router.post("/api/procurement/suppliers")
def create_supplier(payload: SupplierWrite, db: Session = Depends(database.get_db)):
    existing = procurement_service.get_supplier_by_name(db, payload.supplier_name)
    if existing:
        raise HTTPException(status_code=400, detail="Supplier with this name already exists")
    if payload.supplier_code and procurement_service.get_supplier_by_code(db, payload.supplier_code):
        raise HTTPException(status_code=400, detail="Supplier code already exists")

    db_supplier = procurement_service.create_supplier(db, payload)
    return {
        "message": "Supplier created successfully",
        "supplier": procurement_service.get_supplier_management_detail(db, db_supplier.id),
    }


@router.get("/api/procurement/suppliers/{supplier_id}")
def get_supplier_by_id(supplier_id: int, db: Session = Depends(database.get_db)):
    supplier = procurement_service.get_supplier_management_detail(db, supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier


@router.put("/api/procurement/suppliers/{supplier_id}")
def update_supplier(supplier_id: int, payload: SupplierWrite, db: Session = Depends(database.get_db)):
    db_supplier = procurement_service.get_supplier_by_id(db, supplier_id)
    if not db_supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    existing = procurement_service.get_supplier_by_name(db, payload.supplier_name)
    if existing and existing.id != supplier_id:
        raise HTTPException(status_code=400, detail="Supplier with this name already exists")

    if payload.supplier_code:
        code_owner = procurement_service.get_supplier_by_code(db, payload.supplier_code)
        if code_owner and code_owner.id != supplier_id:
            raise HTTPException(status_code=400, detail="Supplier code already exists")

    updated = procurement_service.update_supplier(db, db_supplier, payload)
    return {
        "message": "Supplier updated successfully",
        "supplier": procurement_service.get_supplier_management_detail(db, updated.id),
    }


@router.delete("/api/procurement/suppliers/{supplier_id}")
def delete_supplier(supplier_id: int, db: Session = Depends(database.get_db)):
    db_supplier = (
        db.query(models.Supplier)
        .options(joinedload(models.Supplier.purchase_orders))
        .filter(models.Supplier.id == supplier_id)
        .first()
    )
    if not db_supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    if db_supplier.purchase_orders:
        raise HTTPException(status_code=409, detail="Supplier has purchase orders and cannot be deleted")

    db.delete(db_supplier)
    db.commit()
    return {"message": "Supplier deleted successfully"}


@router.post("/api/procurement/suppliers/{supplier_id}/negotiation-email")
def generate_negotiation_email(supplier_id: int, db: Session = Depends(database.get_db)):
    supplier = procurement_service.get_supplier_by_id(db, supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    recent_pos = (
        db.query(models.PurchaseOrder)
        .filter(models.PurchaseOrder.supplier_id == supplier_id)
        .order_by(models.PurchaseOrder.created_at.desc())
        .limit(5)
        .all()
    )
    total_volume = sum(po.total_value or 0 for po in recent_pos)

    try:
        email_content = ai_service.generate_supplier_email(supplier, len(recent_pos), total_volume)
    except RuntimeError as error:
        raise HTTPException(status_code=500, detail=str(error))

    return {
        "email": email_content,
        "supplier_name": supplier.name,
        "supplier_email": supplier.contact_email,
        "context": {
            "total_pos": len(recent_pos),
            "total_volume": round(total_volume, 2),
            "reliability": procurement_service.get_supplier_reliability_percent(supplier),
        },
    }


@router.get("/api/procurement/purchase-orders")
def list_purchase_orders(
    limit: Optional[int] = None,
    page: int = 1,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    supplier: Optional[str] = None,
    search: Optional[str] = None,
    date_range: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sort: Optional[str] = "latest",
    db: Session = Depends(database.get_db),
):
    query = db.query(models.PurchaseOrder)

    if status:
        query = query.filter(models.PurchaseOrder.status == status.upper())
    if priority:
        query = query.filter(models.PurchaseOrder.priority == priority.title())
    if supplier:
        query = query.join(models.Supplier).filter(models.Supplier.name.ilike(f"%{supplier}%"))
    if search:
        query = query.filter(
            models.PurchaseOrder.po_number.ilike(f"%{search}%")
            | models.PurchaseOrder.product_name.ilike(f"%{search}%")
        )
    if start_date:
        try:
            query = query.filter(models.PurchaseOrder.created_at >= datetime.fromisoformat(start_date))
        except Exception:
            pass
    if end_date:
        try:
            query = query.filter(models.PurchaseOrder.created_at <= datetime.fromisoformat(end_date))
        except Exception:
            pass

    if sort == "oldest":
        query = query.order_by(models.PurchaseOrder.created_at.asc())
    else:
        query = query.order_by(models.PurchaseOrder.created_at.desc())

    if limit:
        query = query.offset(max(page - 1, 0) * limit).limit(limit)

    pos = query.options(joinedload(models.PurchaseOrder.supplier)).all()
    results = []
    for po in pos:
        supplier_row = po.supplier
        created_at = po.created_at or datetime.utcnow()
        results.append({
            "id": str(po.id),
            "poNumber": po.po_number,
            "title": po.product_name or "Procurement Order",
            "supplierName": supplier_row.name if supplier_row else "Unknown Supplier",
            "status": procurement_service.normalize_po_status(po.status),
            "priority": (po.priority or "Medium").title(),
            "lifecycleStage": procurement_service.normalize_po_status(po.status),
            "createdAt": created_at.isoformat(),
            "expectedDelivery": po.expected_delivery.isoformat() if po.expected_delivery else None,
        })
    return results


@router.post("/api/procurement/purchase-orders/create")
def create_purchase_order(payload: QuickPOCreate, db: Session = Depends(database.get_db)):
    product, supplier = procurement_service.resolve_procurement_context(
        db,
        product_id=payload.productId,
        sku=payload.sku,
        supplier_id=payload.supplierId,
        supplier_name=payload.supplierName,
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found for purchase order creation")
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found for purchase order creation")

    db_po = procurement_service.create_purchase_order(
        supplier=supplier,
        product=product,
        product_name=payload.itemName,
        quantity=payload.quantity,
        unit_price=payload.unitPrice,
        priority=payload.priority,
        estimated_lead_time=payload.estimatedLeadTime,
        db=db,
    )
    created_at = db_po.created_at or datetime.utcnow()
    return {
        "id": str(db_po.id),
        "poNumber": db_po.po_number,
        "status": procurement_service.normalize_po_status(db_po.status),
        "createdAt": created_at.isoformat(),
        "previewUrl": f"/api/procurement/purchase-orders/{db_po.id}",
    }


@router.get("/api/procurement/purchase-orders/{po_id}")
def get_purchase_order(po_id: int, db: Session = Depends(database.get_db)):
    db_po = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.id == po_id).first()
    if not db_po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return procurement_service.build_purchase_order_document(db_po, db)


@router.put("/api/procurement/purchase-orders/{po_id}/status")
def update_purchase_order_status(po_id: int, payload: POStatusUpdate, db: Session = Depends(database.get_db)):
    status = (payload.status or "").strip().upper()
    if status not in ["DRAFT", "APPROVED", "IN_TRANSIT", "RECEIVED"]:
        raise HTTPException(status_code=400, detail="Invalid purchase order status")
    db_po = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.id == po_id).first()
    if not db_po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    procurement_service.update_po_status(db, db_po, status)
    return procurement_service.build_purchase_order_document(db_po, db)


@router.get("/api/procurement/purchase-orders/{po_id}/pdf")
def download_purchase_order_pdf(po_id: int, db: Session = Depends(database.get_db)):
    db_po = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.id == po_id).first()
    if not db_po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    document = procurement_service.build_purchase_order_document(db_po, db)
    pdf_bytes = build_purchase_order_pdf(document)
    filename = f"{document['poNumber']}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/procurement/compare/")
def recommend_supplier(request: ProcurementRequest, db: Session = Depends(database.get_db)):
    suppliers = (
        db.query(models.Supplier)
        .filter(models.Supplier.delivery_speed_days <= request.max_days_allowed)
        .order_by(models.Supplier.reliability_score.desc())
        .limit(3)
        .all()
    )

    if not suppliers:
        return {
            "ai_recommendation": (
                f"No suppliers found who can deliver {request.material_name} within "
                f"{request.max_days_allowed} days. Consider extending your lead time requirements."
            )
        }

    best_match = suppliers[0]
    rec_text = f"Top Recommendation: **{best_match.name}**\n\n"
    rec_text += f"- **Reliability Score**: {procurement_service.get_supplier_reliability_percent(best_match)}/100\n"
    rec_text += f"- **Delivery Speed**: {procurement_service.get_supplier_average_delivery_days(best_match)} days\n"
    rec_text += f"They are the most reliable option that meets your {request.max_days_allowed}-day requirement."

    return {"ai_recommendation": rec_text}

# anything
