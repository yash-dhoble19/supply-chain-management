"""
Procurement Automation Service
Handles procurement sessions, n8n integration, communication tracking,
quote management, and ZenRows web scraping for external suppliers.
"""
import json
import os
from datetime import datetime, timezone
from typing import Optional

import requests
from sqlalchemy.orm import Session, joinedload

import models
from services.procurement_service import (
    calculate_supplier_score,
    compose_supplier_location,
    get_supplier_average_delivery_days,
    get_supplier_reliability_percent,
    get_supplier_on_time_percent,
    get_supplier_unit_price,
)
from services.zenrows_scraper import search_external_suppliers


# ── Configuration ────────────────────────────────────────────────

N8N_BASE_URL = os.getenv("N8N_BASE_URL", "https://yash1223456.app.n8n.cloud")
N8N_WEBHOOK_SUPPLIER_INQUIRY = os.getenv("N8N_WEBHOOK_SUPPLIER_INQUIRY", "/webhook/supplier-inquiry")
N8N_WEBHOOK_SECRET = os.getenv("N8N_WEBHOOK_SECRET", "")
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8000")
WEBHOOK_CALLBACK_BASE = os.getenv("WEBHOOK_CALLBACK_BASE", "/api/webhooks")


# ── Session Management ───────────────────────────────────────────

def generate_session_code(db: Session) -> str:
    count = db.query(models.ProcurementSession).count()
    return f"SESS-{datetime.now().strftime('%Y%m')}-{count + 1:04d}"


def create_session(
    db: Session,
    product_name: str,
    product_category: Optional[str] = None,
    search_query: Optional[dict] = None,
    source_types: Optional[str] = None,
) -> models.ProcurementSession:
    session = models.ProcurementSession(
        session_code=generate_session_code(db),
        product_name=product_name,
        product_category=product_category,
        search_query=json.dumps(search_query) if search_query else None,
        source_types=source_types or "internal",
        status="ACTIVE",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session(db: Session, session_id: int) -> Optional[models.ProcurementSession]:
    return (
        db.query(models.ProcurementSession)
        .options(
            joinedload(models.ProcurementSession.email_interactions)
            .joinedload(models.EmailInteraction.supplier),
            joinedload(models.ProcurementSession.quotes),
        )
        .filter(models.ProcurementSession.id == session_id)
        .first()
    )


def list_sessions(db: Session, status: Optional[str] = None) -> list[dict]:
    query = db.query(models.ProcurementSession).order_by(
        models.ProcurementSession.created_at.desc()
    )
    if status:
        query = query.filter(models.ProcurementSession.status == status.upper())
    sessions = query.all()

    results = []
    for s in sessions:
        results.append({
            "id": s.id,
            "session_code": s.session_code,
            "product_name": s.product_name,
            "product_category": s.product_category,
            "status": s.status,
            "total_suppliers_found": s.total_suppliers_found,
            "total_inquiries_sent": s.total_inquiries_sent,
            "total_replies": s.total_replies,
            "total_quotes": s.total_quotes,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        })
    return results


def update_session_counts(db: Session, session_id: int) -> None:
    if not session_id:
        return
    session = db.query(models.ProcurementSession).filter(
        models.ProcurementSession.id == session_id
    ).first()
    if not session:
        return

    interactions = db.query(models.EmailInteraction).filter(
        models.EmailInteraction.session_id == session_id
    ).all()

    session.total_inquiries_sent = sum(
        1 for i in interactions if i.status not in ("inquiry_pending",)
    )
    session.total_replies = sum(
        1 for i in interactions
        if i.status in ("reply_received", "REPLIED", "QUOTE_RECEIVED", "APPROVED")
    )
    session.total_quotes = db.query(models.SupplierQuote).filter(
        models.SupplierQuote.session_id == session_id
    ).count()

    if session.total_quotes > 0:
        session.status = "QUOTES_RECEIVED"
    elif session.total_inquiries_sent > 0:
        session.status = "INQUIRIES_SENT"

    db.commit()


# ── Supplier Search (ZenRows External ONLY) ──────────────────────

def search_suppliers_internal(
    db: Session,
    product_name: str,
    category: Optional[str] = None,
    location: Optional[str] = None,
    max_lead_time_days: Optional[int] = None,
    fetch_external: bool = True,
) -> list[dict]:
    """
    Search for suppliers using ZenRows web scraping ONLY.
    Does NOT query the internal suppliers table.
    Scraped suppliers are saved to DB so n8n can reference them later.
    """

    # ── Step 1: Call ZenRows to scrape external suppliers ──
    external_data = search_external_suppliers(product_name)
    print(f"[Search] ZenRows returned {len(external_data)} suppliers for '{product_name}'")

    # ── Step 2: Save scraped suppliers to DB (for n8n inquiry tracking) ──
    saved_suppliers = []
    for ext in external_data:
        # Check if this supplier already exists by email
        existing = db.query(models.Supplier).filter(
            models.Supplier.contact_email == ext["contact_email"]
        ).first()

        if existing:
            saved_suppliers.append(existing)
        else:
            new_sup = models.Supplier(
                name=ext["company_name"],
                company_name=ext["company_name"],
                contact_person=ext.get("contact_person", "Sales Dept"),
                contact_email=ext["contact_email"],
                phone=ext.get("phone"),
                city=ext.get("city"),
                country=ext.get("country"),
                product_category=ext.get("product_category"),
                product_name=product_name,
                source=ext.get("source", "ZENROWS_WEB"),
                source_url=ext.get("source_url"),
                reliability_score=ext.get("reliability_score", 85),
                average_delivery_days=ext.get("average_delivery_days", 7),
                unit_price=ext.get("unit_price", 0),
                currency=ext.get("currency", "INR"),
                source_scraped_at=datetime.now(timezone.utc),
            )
            db.add(new_sup)
            try:
                db.flush()  # Get the ID immediately
                saved_suppliers.append(new_sup)
            except Exception:
                db.rollback()

    try:
        db.commit()
    except Exception:
        db.rollback()

    # ── Step 3: Build response from scraped data ──
    results = []
    for idx, ext in enumerate(external_data):
        # Find the matching DB record to get the supplier_id
        db_supplier = next(
            (s for s in saved_suppliers if s.contact_email == ext["contact_email"]),
            None
        )
        supplier_id = db_supplier.id if db_supplier else -(idx + 1)

        # Calculate AI score based on reliability + delivery speed
        reliability = ext.get("reliability_score", 85)
        delivery_days = ext.get("average_delivery_days", 7)
        reliability_norm = reliability / 100
        lead_time_norm = max(0, 1 - (delivery_days / 30))
        ai_score = round((reliability_norm * 0.5 + lead_time_norm * 0.5) * 100, 1)

        results.append({
            "supplier_id": supplier_id,
            "name": ext["company_name"],
            "company_name": ext["company_name"],
            "contact_email": ext["contact_email"],
            "contact_person": ext.get("contact_person", "Sales Dept"),
            "phone": ext.get("phone"),
            "location": f"{ext.get('city', '')}, {ext.get('country', '')}".strip(", "),
            "product_name": product_name,
            "product_category": ext.get("product_category", category or "General"),
            "unit_price": ext.get("unit_price", 0),
            "currency": ext.get("currency", "INR"),
            "average_delivery_days": delivery_days,
            "reliability_percent": reliability,
            "on_time_percent": round(reliability - 1.5, 1),
            "ai_score": ai_score,
            "source": ext.get("source", "ZENROWS_WEB"),
            "preferred": False,
            "responsiveness": "NORMAL",
            "status": "ACTIVE",
        })

    results.sort(key=lambda x: x["ai_score"], reverse=True)
    return results


# ── Send Inquiry (Trigger n8n) ───────────────────────────────────

def send_inquiry_to_suppliers(
    db: Session,
    session_id: int,
    supplier_ids: list[int],
    product_name: str,
    quantity: int = 0,
    specs: Optional[str] = None,
) -> dict:
    session = db.query(models.ProcurementSession).filter(
        models.ProcurementSession.id == session_id
    ).first()
    if not session:
        return {"error": "Session not found", "triggered": 0}

    triggered = []
    errors = []

    for supplier_id in supplier_ids:
        supplier = db.query(models.Supplier).filter(
            models.Supplier.id == supplier_id
        ).first()
        if not supplier:
            errors.append({"supplier_id": supplier_id, "error": "Supplier not found"})
            continue

        existing = db.query(models.EmailInteraction).filter(
            models.EmailInteraction.session_id == session_id,
            models.EmailInteraction.supplier_id == supplier_id,
        ).first()
        if existing:
            errors.append({"supplier_id": supplier_id, "error": "Already contacted in session"})
            continue

        interaction = models.EmailInteraction(
            session_id=session_id,
            supplier_id=supplier_id,
            product_name=product_name,
            quantity_requested=quantity,
            specs=specs,
            status="inquiry_pending",
            email_type="inquiry",
        )
        db.add(interaction)
        db.commit()
        db.refresh(interaction)

        log = models.EmailInteractionLog(
            interaction_id=interaction.id,
            event_type="INQUIRY_TRIGGERED",
            event_data=json.dumps({"supplier_name": supplier.name, "product": product_name, "quantity": quantity}),
        )
        db.add(log)
        supplier.last_contacted_at = datetime.now(timezone.utc)
        supplier.total_inquiries_sent = (supplier.total_inquiries_sent or 0) + 1
        db.commit()

        n8n_payload = {
            "supplierId": supplier.id,
            "supplierName": supplier.name,
            "supplierEmail": supplier.contact_email,
            "supplierCompany": supplier.company_name,
            "productName": product_name,
            "quantity": quantity,
            "deadline": "",
            "budget": 0,
            "interaction_id": interaction.id,
            "session_id": str(session_id),
            "session_code": session.session_code,
            "specs": specs or "",
            "callback_base_url": f"{APP_BASE_URL}{WEBHOOK_CALLBACK_BASE}",
        }

        n8n_success = _trigger_n8n_workflow(n8n_payload)

        triggered.append({
            "interaction_id": interaction.id,
            "supplier_id": supplier.id,
            "supplier_name": supplier.name,
            "n8n_triggered": n8n_success,
        })

    update_session_counts(db, session_id)
    return {"triggered": len(triggered), "interactions": triggered, "errors": errors}

def _trigger_n8n_workflow(payload: dict) -> bool:
    url = f"{N8N_BASE_URL}{N8N_WEBHOOK_SUPPLIER_INQUIRY}"
    headers = {"Content-Type": "application/json"}
    if N8N_WEBHOOK_SECRET:
        headers["X-Webhook-Secret"] = N8N_WEBHOOK_SECRET
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        return response.status_code in (200, 201, 204)
    except:
        return False

# ── Webhook Handlers ─────────────────────────────────────────────

def handle_inquiry_sent(db: Session, payload: dict) -> dict:
    message_id = payload.get("messageId")
    thread_id = payload.get("threadId")
    recipient = payload.get("recipient")
    interaction_id = payload.get("interaction_id")

    interaction = None
    if interaction_id:
        interaction = db.query(models.EmailInteraction).filter(models.EmailInteraction.id == interaction_id).first()
    if not interaction and thread_id:
        interaction = db.query(models.EmailInteraction).filter(models.EmailInteraction.thread_id == thread_id).first()

    if not interaction:
        return {"status": "warning", "message": "Interaction not found"}

    interaction.status = "sent"
    interaction.message_id = message_id
    interaction.thread_id = thread_id
    interaction.recipient_email = recipient
    if not interaction.sent_at:
        interaction.sent_at = datetime.now(timezone.utc)

    if payload.get("followUpSent"):
        interaction.status = "follow_up_sent"
        interaction.follow_up_sent_at = datetime.now(timezone.utc)

    log = models.EmailInteractionLog(
        interaction_id=interaction.id,
        event_type="INQUIRY_SENT",
        event_data=json.dumps({"message_id": message_id, "thread_id": thread_id}),
    )
    db.add(log)
    db.commit()
    if interaction.session_id: update_session_counts(db, interaction.session_id)
    return {"status": "ok", "interaction_id": interaction.id}

def handle_supplier_replied(db: Session, payload: dict) -> dict:
    supplier_id_val = payload.get("supplierId")
    sender_email = payload.get("senderEmail")

    supplier = None
    if supplier_id_val:
        supplier = db.query(models.Supplier).filter((models.Supplier.id == supplier_id_val)).first()
    if not supplier:
        return {"status": "warning", "message": "Supplier not matched"}

    interaction = db.query(models.EmailInteraction).filter(
        models.EmailInteraction.supplier_id == supplier.id,
        models.EmailInteraction.status.in_(["sent", "follow_up_sent", "inquiry_pending"])
    ).first()

    if not interaction:
        interaction = models.EmailInteraction(
            supplier_id=supplier.id, status="reply_received", email_type="reply"
        )
        db.add(interaction)
        db.commit()

    interaction.status = "reply_received"
    if payload.get("subject"): interaction.subject = payload["subject"]
    interaction.received_at = datetime.now(timezone.utc)
    interaction.extracted_data = json.dumps(payload.get("extractedQuote") or {})
    supplier.responsiveness_flag = "NORMAL"

    log = models.EmailInteractionLog(
        interaction_id=interaction.id,
        event_type="REPLY_RECEIVED",
        event_data=json.dumps({"sender": sender_email}),
    )
    db.add(log)
    db.commit()
    if interaction.session_id: update_session_counts(db, interaction.session_id)
    return {"status": "ok", "interaction_id": interaction.id}

def handle_followup_sent(db: Session, payload: dict) -> dict:
    thread_id = payload.get("threadId")
    interaction = db.query(models.EmailInteraction).filter(models.EmailInteraction.thread_id == thread_id).first()
    if not interaction: return {"status": "warning"}
    interaction.status = "follow_up_sent"
    interaction.follow_up_sent_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "ok", "interaction_id": interaction.id}

def handle_escalation_alert(db: Session, payload: dict) -> dict:
    thread_id = payload.get("threadId")
    interaction = db.query(models.EmailInteraction).filter(models.EmailInteraction.thread_id == thread_id).first()
    if not interaction: return {"status": "warning"}
    interaction.status = "escalated"
    interaction.escalated_at = datetime.now(timezone.utc)
    db.commit()
    if interaction.session_id: update_session_counts(db, interaction.session_id)
    return {"status": "ok", "interaction_id": interaction.id}

def get_communication_summary(db: Session) -> dict:
    interactions = db.query(models.EmailInteraction).all()
    return {
        "total_inquiries": len(interactions),
        "sent": sum(1 for i in interactions if i.status == "sent"),
        "pending_reply": sum(1 for i in interactions if i.status in ("sent", "follow_up_sent")),
        "replied": sum(1 for i in interactions if i.status == "reply_received"),
    }


def list_interactions(
    db: Session,
    session_id: Optional[int] = None,
    supplier_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    query = (
        db.query(models.EmailInteraction)
        .options(joinedload(models.EmailInteraction.supplier))
        .order_by(models.EmailInteraction.updated_at.desc())
    )
    total = query.count()
    offset = max(0, (page - 1)) * page_size
    interactions = query.offset(offset).limit(page_size).all()
    items = []
    
    def _safe_json_loads(data):
        if not data or not str(data).strip():
            return None
        cleaned = str(data).strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        try:
            return json.loads(cleaned)
        except Exception:
            return None

    for i in interactions:
        s = i.supplier
        parsed_quote = _safe_json_loads(i.extracted_data)
        items.append({
            "interaction_id": i.id,
            "session_id": i.session_id,
            "supplier_id": i.supplier_id,
            "supplier_name": s.name if s else "Unknown",
            "supplier_email": s.contact_email if s else None,
            "product_name": i.product_name,
            "quantity": i.quantity_requested,
            "status": i.status,
            "sent_at": i.sent_at.isoformat() if i.sent_at else None,
            "has_quote": bool(parsed_quote),
            "extracted_quote": parsed_quote,
        })
    return {
        "items": items,
        "pagination": {"page": page, "page_size": page_size, "total_items": total}
    }

def get_interaction_detail(db: Session, interaction_id: int):
    pass
def get_session_quotes(db: Session, session_id: int):
    pass
def approve_supplier(db: Session, supplier_id: int, session_id: int, notes: str):
    pass
