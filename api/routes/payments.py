"""
Payment API Routes
==================
Handles payment recording and invoice generation for retailer orders.
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

import database

router = APIRouter(tags=["Payments"])


class PaymentItemSchema(BaseModel):
    product_name: str
    sku: Optional[str] = None
    quantity: int
    unit_price: float
    category: Optional[str] = None


class PaymentOrderCreate(BaseModel):
    payment_method: str  # "upi" or "cash"
    upi_transaction_id: Optional[str] = None
    retailer_name: str
    retailer_email: str
    retailer_phone: str
    retailer_location: str
    items: List[PaymentItemSchema]
    subtotal: float
    freight: float
    grand_total: float


class InvoiceResponse(BaseModel):
    invoice_id: str
    invoice_number: str
    order_date: str
    payment_method: str
    upi_transaction_id: Optional[str] = None
    retailer_name: str
    retailer_email: str
    retailer_phone: str
    retailer_location: str
    items: List[dict]
    subtotal: float
    freight: float
    grand_total: float
    status: str


@router.post("/payments/create-order", response_model=InvoiceResponse)
def create_payment_order(
    order: PaymentOrderCreate = Body(...),
    db: Session = Depends(database.get_db),
):
    """
    Record a payment order and return an invoice.
    Supports UPI and Cash payment methods.
    """
    if order.payment_method not in ("upi", "cash"):
        raise HTTPException(status_code=400, detail="Invalid payment method. Use 'upi' or 'cash'.")

    if order.payment_method == "upi" and not order.upi_transaction_id:
        raise HTTPException(status_code=400, detail="UPI transaction ID is required for UPI payments.")

    if not order.items:
        raise HTTPException(status_code=400, detail="Order must contain at least one item.")

    # Generate invoice
    now = datetime.utcnow()
    invoice_id = str(uuid.uuid4())
    invoice_number = f"INV-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    items_list = []
    for item in order.items:
        items_list.append({
            "product_name": item.product_name,
            "sku": item.sku or "N/A",
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "category": item.category or "General",
            "line_total": round(item.unit_price * item.quantity, 2),
        })

    return InvoiceResponse(
        invoice_id=invoice_id,
        invoice_number=invoice_number,
        order_date=now.isoformat(),
        payment_method=order.payment_method,
        upi_transaction_id=order.upi_transaction_id,
        retailer_name=order.retailer_name,
        retailer_email=order.retailer_email,
        retailer_phone=order.retailer_phone,
        retailer_location=order.retailer_location,
        items=items_list,
        subtotal=order.subtotal,
        freight=order.freight,
        grand_total=order.grand_total,
        status="paid" if order.payment_method == "upi" else "pending_cash",
    )

# anything
