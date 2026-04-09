"""
AI Tools routes - /api/ai-tools/* and /api/webhooks/*
Supplier Finder, Communication Hub, and n8n Webhook endpoints.

Webhook payloads match n8n's actual HTTP Request node output formats.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

import database
import os
from schemas.ai_tools import (
    ApproveSupplierRequest,
    DashboardConfirmationPayload,
    EscalationAlertPayload,
    FollowupSentPayload,
    SendInquiryRequest,
    SupplierReplyPayload,
    SupplierSearchRequest,
)
from services import procurement_automation_service


router = APIRouter(tags=["AI Tools"])

N8N_WEBHOOK_SECRET = os.getenv("N8N_WEBHOOK_SECRET", "")


def _verify_webhook_secret(request: Request) -> None:
    """Validate webhook secret header from n8n. Skip if not configured."""
    if not N8N_WEBHOOK_SECRET:
        return
    secret = request.headers.get("X-Webhook-Secret", "")
    if secret != N8N_WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")


# ══════════════════════════════════════════════════════════════════
# SUPPLIER SEARCH
# ══════════════════════════════════════════════════════════════════

@router.post("/api/ai-tools/supplier-search")
def search_suppliers(
    payload: SupplierSearchRequest,
    db: Session = Depends(database.get_db),
):
    """Search internal DB for suppliers and create a procurement session."""
    session = procurement_automation_service.create_session(
        db,
        product_name=payload.product_name,
        product_category=payload.category,
        search_query=payload.model_dump(),
        source_types=",".join(payload.sources),
    )

    results = procurement_automation_service.search_suppliers_internal(
        db,
        product_name=payload.product_name,
        category=payload.category,
        location=payload.location,
        max_lead_time_days=payload.max_lead_time_days,
    )

    session.total_suppliers_found = len(results)
    db.commit()

    return {
        "session_id": session.id,
        "session_code": session.session_code,
        "product_name": payload.product_name,
        "total_found": len(results),
        "sources_searched": payload.sources,
        "suppliers": results,
    }


# ══════════════════════════════════════════════════════════════════
# SESSIONS
# ══════════════════════════════════════════════════════════════════

@router.get("/api/ai-tools/sessions")
def get_sessions(
    status: Optional[str] = None,
    db: Session = Depends(database.get_db),
):
    return procurement_automation_service.list_sessions(db, status=status)


@router.get("/api/ai-tools/sessions/{session_id}")
def get_session(session_id: int, db: Session = Depends(database.get_db)):
    session = procurement_automation_service.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "id": session.id,
        "session_code": session.session_code,
        "product_name": session.product_name,
        "product_category": session.product_category,
        "status": session.status,
        "total_suppliers_found": session.total_suppliers_found,
        "total_inquiries_sent": session.total_inquiries_sent,
        "total_replies": session.total_replies,
        "total_quotes": session.total_quotes,
        "approved_supplier_id": session.approved_supplier_id,
        "created_at": session.created_at.isoformat() if session.created_at else None,
    }


# ══════════════════════════════════════════════════════════════════
# SEND INQUIRY (triggers n8n Workflow 1)
# ══════════════════════════════════════════════════════════════════

@router.post("/api/ai-tools/send-inquiry")
def send_inquiry(
    payload: SendInquiryRequest,
    db: Session = Depends(database.get_db),
):
    result = procurement_automation_service.send_inquiry_to_suppliers(
        db,
        session_id=payload.session_id,
        supplier_ids=payload.supplier_ids,
        product_name=payload.product_name,
        quantity=payload.quantity,
        specs=payload.specs,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ══════════════════════════════════════════════════════════════════
# COMMUNICATION STATUS
# ══════════════════════════════════════════════════════════════════

@router.get("/api/ai-tools/communication/status")
def get_communication_status(db: Session = Depends(database.get_db)):
    return procurement_automation_service.get_communication_summary(db)


@router.get("/api/ai-tools/communication/interactions")
def get_interactions(
    session_id: Optional[int] = None,
    supplier_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(database.get_db),
):
    return procurement_automation_service.list_interactions(
        db,
        session_id=session_id,
        supplier_id=supplier_id,
        status=status,
        page=page,
        page_size=page_size,
    )


@router.get("/api/ai-tools/communication/interactions/{interaction_id}")
def get_interaction_detail(
    interaction_id: int,
    db: Session = Depends(database.get_db),
):
    detail = procurement_automation_service.get_interaction_detail(db, interaction_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return detail


# ══════════════════════════════════════════════════════════════════
# QUOTES
# ══════════════════════════════════════════════════════════════════

@router.get("/api/ai-tools/quotes/{session_id}")
def get_session_quotes(session_id: int, db: Session = Depends(database.get_db)):
    return procurement_automation_service.get_session_quotes(db, session_id)


@router.post("/api/ai-tools/suppliers/{supplier_id}/approve")
def approve_supplier(
    supplier_id: int,
    payload: ApproveSupplierRequest,
    db: Session = Depends(database.get_db),
):
    result = procurement_automation_service.approve_supplier(
        db,
        supplier_id=supplier_id,
        session_id=payload.session_id,
        notes=payload.notes,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ══════════════════════════════════════════════════════════════════
# WEBHOOK ENDPOINTS (n8n calls these)
# Payload formats match n8n's actual HTTP Request node outputs.
# ══════════════════════════════════════════════════════════════════

@router.post("/api/webhooks/inquiry-sent")
async def webhook_inquiry_sent(
    payload: DashboardConfirmationPayload,
    request: Request,
    db: Session = Depends(database.get_db),
):
    """
    Called by n8n 'Send Dashboard Confirmation' node (Workflow 1).
    Receives: status, messageId, threadId, recipient, timestamp,
    replyReceived, followUpSent, nextReminderTime
    """
    _verify_webhook_secret(request)
    result = procurement_automation_service.handle_inquiry_sent(db, payload.model_dump())
    return result


@router.post("/api/webhooks/supplier-replied")
async def webhook_supplier_replied(
    payload: SupplierReplyPayload,
    request: Request,
    db: Session = Depends(database.get_db),
):
    """
    Called by n8n 'Notify Dashboard' node (Workflow 2).
    Receives: supplierId, companyName, senderEmail, subject,
    receivedAt, emailBody, extractedQuote
    """
    _verify_webhook_secret(request)
    result = procurement_automation_service.handle_supplier_replied(db, payload.model_dump())
    return result


@router.post("/api/webhooks/followup-sent")
async def webhook_followup_sent(
    payload: FollowupSentPayload,
    request: Request,
    db: Session = Depends(database.get_db),
):
    """
    Called by n8n 'Notify Dashboard - Follow-up Sent' node (Workflow 3).
    Receives: supplierId, companyName, followUpSent, sentAt,
    responseDeadline, threadId
    """
    _verify_webhook_secret(request)
    result = procurement_automation_service.handle_followup_sent(db, payload.model_dump())
    return result


@router.post("/api/webhooks/escalation-alert")
async def webhook_escalation_alert(
    payload: EscalationAlertPayload,
    request: Request,
    db: Session = Depends(database.get_db),
):
    """
    Called by n8n 'Send Escalation Alert' node (Workflow 3).
    Receives: alertType, supplierId, companyName, threadId,
    hoursSinceInquiry, recommendation, escalatedAt
    """
    _verify_webhook_secret(request)
    result = procurement_automation_service.handle_escalation_alert(db, payload.model_dump())
    return result

# anything
