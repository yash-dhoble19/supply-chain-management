"""
Procurement routes — /api/procurement/*, /procurement/suppliers/create
Consolidates all procurement endpoints. Streamlit-only duplicates removed.
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
import models
import database
from schemas.procurement import SupplierCreate, QuickPOCreate, POStatusUpdate, ProcurementRequest
from services import procurement_service, ai_service
from services.pdf_service import build_purchase_order_pdf

router = APIRouter(tags=["Procurement"])


# ── Summary & Insights ───────────────────────────────────────────────


@router.get("/api/procurement/summary")
def get_summary(db: Session = Depends(database.get_db)):
    health_score = procurement_service.calculate_supply_chain_health_score(db)
    from sqlalchemy.orm import joinedload
    products = db.query(models.Product).options(
        joinedload(models.Product.po_items).joinedload(models.POItem.purchase_order)
    ).all()
    suppliers = db.query(models.Supplier).all()

    pending_pos = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.status == "DRAFT").count()
    approved_pos = db.query(models.PurchaseOrder).filter(
        models.PurchaseOrder.status.in_(["APPROVED", "IN_TRANSIT"])
    ).count()

    critical_items = 0
    critical_names = []
    for product in products:
        po_items = getattr(product, "po_items", [])
        incoming_qty = sum(
            item.quantity_ordered for item in po_items
            if item.purchase_order and item.purchase_order.status in ["DRAFT", "APPROVED", "IN_TRANSIT"]
        )
        if (product.current_stock + incoming_qty) < (product.optimal_stock_level * 0.2):
            critical_items += 1
            if len(critical_names) < 2:
                critical_names.append(product.name)

    insights = procurement_service.build_procurement_insights(db, limit=12)
    product_lookup = {p.id: p for p in products}

    savings_to_date = round(
        sum(
            max(0, (product_lookup[i["productId"]].unit_price or 0) - i["unitPrice"]) * i["replenishmentQty"]
            for i in insights
            if i["productId"] in product_lookup and i["actionType"] == "quick_po"
        ), 2,
    )

    avg_supplier_lead = round(sum(s.delivery_speed_days or 0 for s in suppliers) / len(suppliers)) if suppliers else 0
    fastest_lead = min((s.delivery_speed_days or 0 for s in suppliers), default=avg_supplier_lead)
    lead_opportunity = max(avg_supplier_lead - fastest_lead, 0)
    projected_spend = sum(i["estimatedCost"] for i in insights if i["actionType"] == "quick_po")
    savings_pct = round((savings_to_date / max(projected_spend, 1)) * 100, 1)
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


@router.get("/api/procurement/bootstrap")
def get_procurement_bootstrap(db: Session = Depends(database.get_db)):
    supplier_response = get_suppliers_overview(db)
    return {
        "summary": get_summary(db),
        "insights": get_insights(None, db),
        "supplierOverview": supplier_response["overview"],
        "supplierRows": supplier_response["suppliers"],
        "topPerformers": get_top_performers(db),
        "spendOptimization": get_spend_optimization(db),
        "purchaseOrders": list_purchase_orders(limit=4, page=1, db=db),
    }


@router.get("/api/procurement/insights")
def get_insights(priority: Optional[str] = None, db: Session = Depends(database.get_db)):
    insights = procurement_service.build_procurement_insights(db, limit=12)
    if priority and priority.lower() != "all":
        insights = [i for i in insights if i["priority"] == priority.lower()]
    return insights


# ── Supplier Endpoints ───────────────────────────────────────────────


@router.post("/procurement/suppliers/create")
def create_supplier(supplier: SupplierCreate, db: Session = Depends(database.get_db)):
    existing = procurement_service.get_supplier_by_name(db, supplier.name)
    if existing:
        raise HTTPException(status_code=400, detail="Supplier with this name already exists")
    db_supplier = procurement_service.create_supplier(
        db, supplier.name, supplier.contact_email, supplier.category,
        supplier.reliability_score, supplier.delivery_speed_days, supplier.price_per_unit,
    )
    trust_score = procurement_service.calculate_supplier_score(db_supplier)
    return {"message": "Supplier created successfully", "supplier_id": db_supplier.id, "initial_trust_score": trust_score}


@router.get("/api/procurement/suppliers/overview")
def get_suppliers_overview(db: Session = Depends(database.get_db)):
    analysis = procurement_service.build_supplier_analysis(db)
    avg_reliability = round(sum(i["reliability"] for i in analysis) / len(analysis), 1) if analysis else 0.0
    on_time_delivery = round(sum(i["onTimeDelivery"] for i in analysis) / len(analysis), 1) if analysis else 0.0
    quality_rate = round(sum(i["qualityRate"] for i in analysis) / len(analysis), 1) if analysis else 0.0
    average_score = round(sum(i["score"] for i in analysis) / len(analysis), 1) if analysis else 0.0

    esg = "A+" if average_score >= 95 else "A" if average_score >= 90 else "B+" if average_score >= 80 else "B"
    return {
        "overview": {"avgReliability": avg_reliability, "onTimeDelivery": on_time_delivery,
                     "qualityRate": quality_rate, "esgCompliance": esg},
        "suppliers": analysis,
    }


@router.get("/api/procurement/suppliers/top-performers")
def get_top_performers(db: Session = Depends(database.get_db)):
    analysis = sorted(procurement_service.build_supplier_analysis(db), key=lambda x: x["score"], reverse=True)[:3]
    performers = []
    for idx, s in enumerate(analysis, start=1):
        metric = (f"{s['qualityRate']}% Quality" if idx == 1
                  else f"{s['onTimeDelivery']}% On-time" if idx == 2
                  else f"{s['reliability']}% Reliability")
        performers.append({"id": s["id"], "rank": idx, "name": s["name"], "metricLabel": metric, "score": s["score"]})
    return performers


@router.get("/api/procurement/spend-optimization")
def get_spend_optimization(db: Session = Depends(database.get_db)):
    insights = procurement_service.build_procurement_insights(db, limit=20)
    product_lookup = {p.id: p for p in db.query(models.Product).all()}

    baseline_spend = sum(i["replenishmentQty"] * (product_lookup.get(i["productId"], models.Product()).unit_price or 0) for i in insights)
    optimized_spend = sum(i["estimatedCost"] for i in insights)
    total_value = round(max(0, baseline_spend - optimized_spend), 2)
    budget_pool = optimized_spend + max(total_value * 4, optimized_spend * 0.2, 1)
    budget_utilization = round((optimized_spend / budget_pool) * 100, 1) if budget_pool else 0.0

    return {
        "totalValue": total_value,
        "yoyChange": f"+{round((total_value / max(baseline_spend, 1)) * 100, 1)}% projected",
        "budgetUtilization": budget_utilization,
        "buttonLabel": "Download Report",
    }


@router.post("/procurement/suppliers/{supplier_id}/negotiation_email")
def generate_negotiation_email(supplier_id: int, db: Session = Depends(database.get_db)):
    supplier = procurement_service.get_supplier_by_id(db, supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    recent_pos = db.query(models.PurchaseOrder).filter(
        models.PurchaseOrder.supplier_id == supplier_id
    ).order_by(models.PurchaseOrder.created_at.desc()).limit(5).all()
    total_volume = sum(po.total_value or 0 for po in recent_pos)

    try:
        email_content = ai_service.generate_supplier_email(supplier, len(recent_pos), total_volume)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "email": email_content, "supplier_name": supplier.name,
        "supplier_email": supplier.contact_email,
        "context": {"total_pos": len(recent_pos), "total_volume": round(total_volume, 2), "reliability": supplier.reliability_score},
    }


# ── Purchase Order CRUD ──────────────────────────────────────────────


@router.get("/api/procurement/purchase-orders")
def list_purchase_orders(
    limit: Optional[int] = None, page: int = 1,
    status: Optional[str] = None, priority: Optional[str] = None,
    supplier: Optional[str] = None, search: Optional[str] = None,
    date_range: Optional[str] = None, start_date: Optional[str] = None,
    end_date: Optional[str] = None, sort: Optional[str] = "latest",
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
        query = query.limit(limit)

    pos = query.all()
    results = []
    # Batch-load suppliers to avoid N+1
    supplier_lookup = {s.id: s for s in db.query(models.Supplier).all()}

    for po in pos:
        s = supplier_lookup.get(po.supplier_id)
        created_at = po.created_at or datetime.utcnow()
        results.append({
            "id": str(po.id), "poNumber": po.po_number,
            "title": po.product_name or "Procurement Order",
            "supplierName": s.name if s else "Unknown Supplier",
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
        db, product_id=payload.productId, sku=payload.sku,
        supplier_id=payload.supplierId, supplier_name=payload.supplierName,
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found for purchase order creation")
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found for purchase order creation")

    db_po = procurement_service.create_purchase_order(
        supplier=supplier, product=product, product_name=payload.itemName,
        quantity=payload.quantity, unit_price=payload.unitPrice,
        priority=payload.priority, estimated_lead_time=payload.estimatedLeadTime, db=db,
    )
    created_at = db_po.created_at or datetime.utcnow()
    return {
        "id": str(db_po.id), "poNumber": db_po.po_number,
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
        content=pdf_bytes, media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/procurement/compare/")
def recommend_supplier(request: ProcurementRequest, db: Session = Depends(database.get_db)):
    # Search DB for suppliers instead of AI hallucination
    suppliers = db.query(models.Supplier).filter(
        models.Supplier.delivery_speed_days <= request.max_days_allowed
    ).order_by(models.Supplier.reliability_score.desc()).limit(3).all()

    if not suppliers:
        return {"ai_recommendation": f"No suppliers found who can deliver {request.material_name} within {request.max_days_allowed} days. Consider extending your lead time requirements."}

    best_match = suppliers[0]
    rec_text = f"Top Recommendation: **{best_match.name}**\n\n"
    rec_text += f"- **Reliability Score**: {best_match.reliability_score}/100\n"
    rec_text += f"- **Delivery Speed**: {best_match.delivery_speed_days} days\n"
    rec_text += f"They are the most reliable option that meets your {request.max_days_allowed}-day requirement."
    
    return {"ai_recommendation": rec_text}
