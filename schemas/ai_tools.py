"""
Pydantic schemas for the AI Procurement Automation Tool endpoints.
Aligned with n8n's actual payload formats.
"""
from pydantic import BaseModel
from typing import Optional, Any


# ── Supplier Search ──────────────────────────────────────────────

class SupplierSearchRequest(BaseModel):
    product_name: str
    category: Optional[str] = None
    location: Optional[str] = None
    max_lead_time_days: Optional[int] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    sources: list[str] = ["internal"]


# ── Send Inquiry ─────────────────────────────────────────────────

class SendInquiryRequest(BaseModel):
    session_id: int
    supplier_ids: list[int]
    product_name: str
    quantity: int = 0
    specs: Optional[str] = None
    deadline: Optional[str] = None
    budget: Optional[float] = None


# ── Webhook Payloads (received from n8n) ─────────────────────────
# These match the EXACT format n8n's HTTP Request nodes send.

class DashboardConfirmationPayload(BaseModel):
    """From n8n 'Send Dashboard Confirmation' node (Workflow 1)"""
    status: Optional[str] = None
    messageId: Optional[str] = None
    threadId: Optional[str] = None
    recipient: Optional[str] = None
    timestamp: Optional[str] = None
    replyReceived: Optional[bool] = None
    followUpSent: Optional[bool] = None
    nextReminderTime: Optional[str] = None
    # Extra fields we pass through callback_base_url
    interaction_id: Optional[int] = None

    class Config:
        extra = "allow"


class SupplierReplyPayload(BaseModel):
    """From n8n 'Notify Dashboard' node (Workflow 2)"""
    supplierId: Optional[int] = None
    companyName: Optional[str] = None
    senderEmail: Optional[str] = None
    subject: Optional[str] = None
    receivedAt: Optional[str] = None
    emailBody: Optional[str] = None
    extractedQuote: Optional[Any] = None

    class Config:
        extra = "allow"


class FollowupSentPayload(BaseModel):
    """From n8n 'Notify Dashboard - Follow-up Sent' node (Workflow 3)"""
    supplierId: Optional[int] = None
    companyName: Optional[str] = None
    followUpSent: Optional[bool] = None
    sentAt: Optional[str] = None
    responseDeadline: Optional[str] = None
    threadId: Optional[str] = None

    class Config:
        extra = "allow"


class EscalationAlertPayload(BaseModel):
    """From n8n 'Send Escalation Alert' node (Workflow 3)"""
    alertType: Optional[str] = None
    supplierId: Optional[int] = None
    companyName: Optional[str] = None
    threadId: Optional[str] = None
    hoursSinceInquiry: Optional[float] = None
    recommendation: Optional[str] = None
    escalatedAt: Optional[str] = None

    class Config:
        extra = "allow"


# ── Supplier Approval ────────────────────────────────────────────

class ApproveSupplierRequest(BaseModel):
    session_id: int
    notes: Optional[str] = None

# anything
