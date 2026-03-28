from fastapi import FastAPI, Depends, HTTPException, UploadFile, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from decimal import Decimal
from openai import OpenAI
import models, database
import pandas as pd
import io
import json
import os
import traceback
from dotenv import load_dotenv
import openai
from geopy.geocoders import Nominatim
import requests
import re

from data_preparation import prepare_category_data, get_data_summary
from forecast_service import run_demand_forecast
from ai_insight_service import generate_ai_insight
from evaluation import evaluate_forecast_accuracy, get_model_diagnostics
from config import settings, get_festivals_for_month, validate_forecast_horizon
from ai_agent import SupplyChainAgent

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Adaptive AI-powered demand forecasting with comprehensive insights"
)

# FIXED CORS - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --- 1. CONFIGURATION & SETUP ---
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = OpenAI(
    api_key=GROQ_API_KEY, 
    base_url="https://api.groq.com/openai/v1"
)

# Initialize Database
models.Base.metadata.create_all(bind=database.engine)

# Initialize Geocoder
geolocator = Nominatim(user_agent="scm_app_free_v1")

# --- 2. SCHEMAS ---

# Product Schemas
class ProductCreate(BaseModel):
    sku: str
    name: str
    category: str
    stage: str
    current_stock: int
    safety_stock_level: int
    optimal_stock_level: int
    unit_price: float

class ProductUpdate(BaseModel):
    sku: Optional[str] = None
    name: Optional[str] = None
    category: Optional[str] = None
    stage: Optional[str] = None
    current_stock: Optional[int] = None
    safety_stock_level: Optional[int] = None
    optimal_stock_level: Optional[int] = None
    unit_price: Optional[float] = None

class StockMovement(BaseModel):
    product_id: int
    quantity_change: int
    reason: str 

# Supplier Schemas
class SupplierCreate(BaseModel):
    name: str
    contact_email: str
    category: str
    reliability_score: float = 95.0
    delivery_speed_days: int = 5
    price_per_unit: float = 10.0

# Purchase Order Schemas
class POCreate(BaseModel):
    supplier_id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    priority: str = "Medium"

class QuickPOCreate(BaseModel):
    insightId: str
    sku: str
    itemName: str
    unitPrice: float
    quantity: int
    supplierName: str
    estimatedLeadTime: Optional[str] = None
    supplierId: Optional[int] = None
    productId: Optional[int] = None
    priority: str = "High"
    notes: Optional[str] = None

class POStatusUpdate(BaseModel):
    status: str

# AI Feature Schemas
class AIProductParseRequest(BaseModel):
    description: str

class PricingRequest(BaseModel):
    product_name: str
    current_price: float
    current_stock: int
    optimal_stock: int
    category: str

class InventoryReportRequest(BaseModel):
    products: List[dict]

class OrderCreate(BaseModel):
    customer_name: str
    delivery_address: str
    order_source: str 

class OrderResponse(BaseModel):
    id: int
    customer_name: str
    delivery_address: Optional[str] = None
    status: str
    ai_risk_assessment: Optional[str] = None
    created_at: Optional[datetime] = None 
    class Config:
        from_attributes = True

class ProcurementRequest(BaseModel):
    material_name: str
    quantity: int
    max_days_allowed: int

class SimulationRequest(BaseModel):
    scenario: str
    products: List[dict]

class ReorderRequest(BaseModel):
    product_name: str
    supplier_name: str = "Valued Supplier"
    current_stock: int
    optimal_stock: int
    unit_price: float

class RouteRequest(BaseModel):
    start_address: str
    end_address: str
    waypoints: List[str] = []

class CarrierCreate(BaseModel):
    name: str
    contact_info: Optional[str] = None
    fleet_size: int = 1
    rating: float = 4.5

class DriverCreate(BaseModel):
    name: str
    license_number: str
    status: str = "AVAILABLE"
    carrier_id: int

class ShipmentCreate(BaseModel):
    tracking_number: str
    origin: str
    destination: str
    carrier_id: Optional[int] = None
    driver_id: Optional[int] = None
    waypoints: List[str] = []
    scheduled_date: Optional[str] = None # ISO format string

class ShipmentUpdate(BaseModel):
    status: Optional[str] = None
    current_location_lat: Optional[float] = None
    current_location_lon: Optional[float] = None
    progress_percent: Optional[float] = None

class AgentRouteRequest(BaseModel):
    intent: str
    payload: dict

# --- 3. HELPER FUNCTIONS ---

def analyze_order_with_groq(address):
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "Risk Manager. Mark HIGH/LOW RISK."}, {"role": "user", "content": address}]
        )
        return response.choices[0].message.content
    except openai.RateLimitError:
        return "AI Rate Limit Reached. Please try again later."
    except Exception: 
        return "AI Error"

def compare_suppliers_with_groq(material, max_days):
    try:
        prompt = f"Buy {material} in {max_days} days. Pick best supplier."
        response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
        return response.choices[0].message.content
    except openai.RateLimitError:
        return "AI Rate Limit Reached. Please try again later."
    except Exception: 
        return "AI Error"

def analyze_market_factors_with_groq(category, trend):
    prompt = f"Category: {category}. Trend: {trend}%. Output JSON with ai_adjustment_factor, insight_text, external_factors."
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "Output JSON only."}, {"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content
    except: return '{"ai_adjustment_factor": 1.0}'

def get_coordinates(address):
    try:
        location = geolocator.geocode(address)
        if location:
            return location.latitude, location.longitude
        return None, None
    except Exception as e:
        return None, None

def get_route_data(start_coords, end_coords, waypoint_coords=None):
    # Construct coordinates string: start;way1;way2;...;end
    coords = [start_coords]
    if waypoint_coords:
        coords.extend(waypoint_coords)
    coords.append(end_coords)
    
    coord_str = ";".join([f"{c[1]},{c[0]}" for c in coords])
    
    url = f"http://router.project-osrm.org/route/v1/driving/{coord_str}?overview=full"
    
    try:
        response = requests.get(url)
        data = response.json()
        if data["code"] == "Ok":
            route = data["routes"][0]
            
            # Simple fuel estimation logic
            distance_km = route["distance"] / 1000
            estimated_fuel_cost = distance_km * 1.5  # Approx $1.5 per km
            
            return {
                "distance_km": round(distance_km, 2),
                "duration_min": round(route["duration"] / 60, 0),
                "geometry": route["geometry"],
                "estimated_cost": round(estimated_fuel_cost, 2)
            }
        return None
    except:
        return None

def parse_product_info_local(description: str):
    text = description.lower()
    
    # 1. Clean Name (remove command words like 'add', 'create', 'please')
    name = description.strip()
    name = re.sub(r"^(?i)(add|create|insert|new|please|make)\s+", "", name)
    name = re.sub(r"\s+per\s+unit.*$", "", name, flags=re.IGNORECASE)
    
    # 2. Category Detection
    category = "Raw Material"
    if any(k in text for k in ["finished", "final", "complete"]):
        category = "Finished Good"
    elif "packaging" in text:
        category = "Packaging"
    elif any(k in text for k in ["component", "part", "assembly"]):
        category = "Component"
    elif any(k in text for k in ["metal", "sheet", "steel", "iron", "wood", "plastic"]):
        category = "Raw Material"
    
    stage = category
    
    # 3. Stock/Quantity Detection (Add 'sheets', 'items', etc)
    stock = 0
    stock_match = re.search(r"(\d+)\s*(?:stock|qty|quantity|units|pcs|sheets|items|pieces|boxes)", text)
    if stock_match:
        stock = int(stock_match.group(1))
    else:
        # Fallback to any standalone number if stock not found with a keyword
        numbers = re.findall(r"\b\d+\b", text)
        if numbers:
            stock = int(numbers[0])
            
    # 4. Price Detection (Add 'dollars', 'rs', 'per unit')
    price = 0.1  # Default to avoid frontend min_value=1.0 errors if they exist
    
    # Look for patterns like "$20", "20 dollars", "20 per unit"
    price_patterns = [
        r"(?:rs\.?|inr|\$)\s*([0-9]+(?:\.[0-9]+)?)",
        r"([0-9]+(?:\.[0-9]+)?)\s*(?:dollars?|bucks?|usd)",
        r"([0-9]+(?:\.[0-9]+)?)\s*per\s*unit",
        r"(?:price|cost)[:\s]*([0-9]+(?:\.[0-9]+)?)"
    ]
    
    for pattern in price_patterns:
        m = re.search(pattern, text)
        if m:
            price = float(m.group(1))
            break
            
    # Calculate sensible defaults
    optimal = stock if stock > 0 else 100
    optimal = int(max(optimal, round(optimal * 1.2)))
    safety = int(round(optimal * 0.2))
    
    return {
        "name": name,
        "category": category,
        "stage": stage,
        "current_stock": stock,
        "unit_price": price,
        "optimal_stock_level": optimal,
        "safety_stock_level": safety
    }

# --- NEW: PROCUREMENT-SPECIFIC HELPER FUNCTIONS ---

def calculate_supply_chain_health_score(db: Session):
    """
    Calculates a comprehensive health score (0-100) based on:
    - Critical stock items
    - Pending POs
    - Supplier reliability
    """
    products = db.query(models.Product).all()
    suppliers = db.query(models.Supplier).all()
    pending_pos = db.query(models.PurchaseOrder).filter(
        models.PurchaseOrder.status.in_(["DRAFT", "APPROVED"])
    ).count()
    
    # Calculate critical items (< 20% of optimal)
    critical_items = sum(1 for p in products if p.current_stock < (p.optimal_stock_level * 0.2))
    critical_penalty = min(critical_items * 5, 40)  # Max 40 points penalty
    
    # Pending PO penalty
    po_penalty = min(pending_pos * 3, 20)  # Max 20 points penalty
    
    # Supplier reliability (average)
    avg_reliability = sum(s.reliability_score for s in suppliers) / len(suppliers) if suppliers else 90
    supplier_bonus = (avg_reliability - 80) / 2  # Bonus if above 80
    
    health_score = 100 - critical_penalty - po_penalty + supplier_bonus
    return max(0, min(100, health_score))


PURCHASE_ORDER_TAX_RATE = 18.0
PURCHASE_ORDER_COMPANY = {
    "companyName": "ChainMind Supply Intelligence",
    "companyAddress": "Procurement Operations, Innovation District, Pune, India",
    "billToCompany": "ChainMind Manufacturing Group",
    "billToAddress": "Accounts Payable, Global Supply Tower, Pune, India",
    "contactEmail": "procurement@chainmind.ai",
}


def _generate_po_number(db: Session) -> str:
    po_count = db.query(models.PurchaseOrder).count()
    return f"PO-{datetime.now().strftime('%Y%m')}-{po_count + 1:04d}"


def _extract_lead_time_days(estimated_lead_time: Optional[str], fallback_days: int) -> int:
    if estimated_lead_time:
        match = re.search(r"(\d+)", estimated_lead_time)
        if match:
            return max(int(match.group(1)), 1)
    return max(fallback_days or 1, 1)


def _resolve_procurement_context(payload: QuickPOCreate, db: Session):
    product = None
    supplier = None

    if payload.productId is not None:
        product = db.query(models.Product).filter(models.Product.id == payload.productId).first()
    if product is None:
        product = db.query(models.Product).filter(models.Product.sku == payload.sku).first()

    if payload.supplierId is not None:
        supplier = db.query(models.Supplier).filter(models.Supplier.id == payload.supplierId).first()
    if supplier is None:
        supplier = db.query(models.Supplier).filter(models.Supplier.name == payload.supplierName).first()

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found for purchase order creation")
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found for purchase order creation")

    return product, supplier


def _normalize_purchase_order_status(status: str) -> str:
    normalized = (status or "DRAFT").strip().upper()
    mapping = {
        "DRAFT": "draft",
        "APPROVED": "approved",
        "IN_TRANSIT": "in_transit",
        "RECEIVED": "received",
    }
    return mapping.get(normalized, "draft")


def _wrap_pdf_text(text: str, width: int = 72) -> List[str]:
    words = text.split()
    if not words:
        return [""]

    lines = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if len(candidate) <= width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _build_purchase_order_document(db_po: models.PurchaseOrder, db: Session):
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
        if db_po.expected_delivery_date
        else None
    )

    return {
        "id": str(db_po.id),
        "poNumber": db_po.po_number,
        "issueDate": created_at.isoformat(),
        "deliveryDate": expected_delivery.isoformat() if expected_delivery else None,
        "status": _normalize_purchase_order_status(db_po.status),
        "supplierName": supplier.name if supplier else "Unknown supplier",
        "supplierAddress": (
            f"{supplier.category} sourcing partner hub" if supplier and supplier.category else "Supplier address pending"
        ),
        "supplierEmail": supplier.contact_email if supplier else PURCHASE_ORDER_COMPANY["contactEmail"],
        "companyName": PURCHASE_ORDER_COMPANY["companyName"],
        "companyAddress": PURCHASE_ORDER_COMPANY["companyAddress"],
        "billToCompany": PURCHASE_ORDER_COMPANY["billToCompany"],
        "billToAddress": PURCHASE_ORDER_COMPANY["billToAddress"],
        "priority": db_po.priority or "Medium",
        "notes": (
            f"Auto-generated from procurement insight workflow. Priority: {db_po.priority}. "
            f"Please confirm supplier availability before dispatch."
        ),
        "subtotal": subtotal,
        "taxRate": PURCHASE_ORDER_TAX_RATE,
        "tax": tax,
        "total": total,
        "items": items,
        "createdAt": created_at.isoformat(),
        "previewUrl": f"/api/procurement/purchase-orders/{db_po.id}",
    }


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _pdf_text(commands: List[str], x: float, y: float, text: str, size: int = 12, bold: bool = False):
    font_name = "F2" if bold else "F1"
    commands.append(
        f"BT /{font_name} {size} Tf 1 0 0 1 {x:.2f} {y:.2f} Tm ({_pdf_escape(text)}) Tj ET"
    )


def _build_purchase_order_pdf(document: dict) -> bytes:
    commands: List[str] = []
    commands.append("0.09 0.29 0.78 rg 40 720 532 48 re f")
    commands.append("1 1 1 rg")
    _pdf_text(commands, 56, 750, document["companyName"], size=19, bold=True)
    _pdf_text(commands, 56, 732, "Purchase Order", size=11, bold=False)
    commands.append("0 g")

    _pdf_text(commands, 420, 750, document["poNumber"], size=15, bold=True)
    _pdf_text(commands, 420, 734, f"Issue Date: {document['issueDate'][:10]}", size=10)
    if document.get("deliveryDate"):
        _pdf_text(commands, 420, 720, f"Delivery: {document['deliveryDate'][:10]}", size=10)

    _pdf_text(commands, 40, 690, "Supplier", size=11, bold=True)
    _pdf_text(commands, 320, 690, "Bill To", size=11, bold=True)
    commands.append("0.85 G 40 682 m 572 682 l S")

    supplier_lines = [
        document["supplierName"],
        document.get("supplierAddress") or "",
        document.get("supplierEmail") or "",
    ]
    bill_lines = [
        document["billToCompany"],
        document["billToAddress"],
        document["companyAddress"],
    ]

    y_supplier = 664
    for line in supplier_lines:
        if line:
            _pdf_text(commands, 40, y_supplier, line, size=10, bold=(y_supplier == 664))
            y_supplier -= 16

    y_bill = 664
    for line in bill_lines:
        if line:
            _pdf_text(commands, 320, y_bill, line, size=10, bold=(y_bill == 664))
            y_bill -= 16

    commands.append("0.95 g 40 576 532 24 re f")
    commands.append("0 g")
    _pdf_text(commands, 52, 584, "Description", size=10, bold=True)
    _pdf_text(commands, 275, 584, "Qty", size=10, bold=True)
    _pdf_text(commands, 355, 584, "Rate", size=10, bold=True)
    _pdf_text(commands, 455, 584, "Amount", size=10, bold=True)

    y_row = 556
    for item in document["items"][:6]:
        _pdf_text(commands, 52, y_row, f"{item['description']} ({item.get('sku', 'N/A')})", size=10)
        _pdf_text(commands, 280, y_row, str(item["quantity"]), size=10)
        _pdf_text(commands, 355, y_row, f"${item['rate']:.2f}", size=10)
        _pdf_text(commands, 455, y_row, f"${item['amount']:.2f}", size=10)
        commands.append(f"0.88 G 40 {y_row - 8:.2f} m 572 {y_row - 8:.2f} l S")
        y_row -= 24

    totals_top = max(y_row - 18, 420)
    _pdf_text(commands, 360, totals_top, "Subtotal", size=10, bold=True)
    _pdf_text(commands, 455, totals_top, f"${document['subtotal']:.2f}", size=10)
    _pdf_text(commands, 360, totals_top - 20, f"Tax ({document['taxRate']:.0f}%)", size=10, bold=True)
    _pdf_text(commands, 455, totals_top - 20, f"${document['tax']:.2f}", size=10)
    commands.append("0.09 0.29 0.78 rg 350 368 190 30 re f")
    commands.append("1 1 1 rg")
    _pdf_text(commands, 364, 378, "Total", size=11, bold=True)
    _pdf_text(commands, 455, 378, f"${document['total']:.2f}", size=11, bold=True)
    commands.append("0 g")

    _pdf_text(commands, 40, 334, "Notes", size=11, bold=True)
    commands.append("0.90 G 40 326 m 572 326 l S")
    note_y = 306
    for line in _wrap_pdf_text(document.get("notes") or "", width=82)[:4]:
        _pdf_text(commands, 40, note_y, line, size=10)
        note_y -= 15

    _pdf_text(commands, 40, 104, "Generated by ChainMind Procurement Intelligence", size=9)

    stream = "\n".join(commands).encode("latin-1", "replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> /Contents 6 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
        b"<< /Length "
        + str(len(stream)).encode("latin-1")
        + b" >>\nstream\n"
        + stream
        + b"\nendstream",
    ]

    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("latin-1"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_start = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
    pdf.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_start}\n%%EOF"
        ).encode("latin-1")
    )
    return bytes(pdf)


def _create_purchase_order_record(
    *,
    supplier: models.Supplier,
    product: models.Product,
    product_name: str,
    quantity: int,
    unit_price: float,
    priority: str,
    estimated_lead_time: Optional[str],
    db: Session,
):
    po_number = _generate_po_number(db)
    lead_time_days = _extract_lead_time_days(estimated_lead_time, supplier.delivery_speed_days)
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

def calculate_supplier_score(supplier, product_price=None):
    """
    Smart supplier scoring algorithm:
    - Reliability: 40%
    - Lead Time (inverse): 30%
    - Price (inverse): 30%
    """
    # Normalize reliability (0-100 to 0-1)
    reliability_norm = supplier.reliability_score / 100
    
    # Normalize lead time (inverse - faster is better)
    # Assuming 1 day is best, 30 days is worst
    lead_time_norm = max(0, 1 - (supplier.delivery_speed_days / 30))
    
    # Normalize price if provided
    if product_price:
        price_norm = max(0, 1 - (supplier.price_per_unit / (product_price * 2)))
    else:
        price_norm = 0.7  # Default neutral score
    
    # Weighted score
    score = (reliability_norm * 0.4) + (lead_time_norm * 0.3) + (price_norm * 0.3)
    return round(score * 100, 2)

def find_best_supplier_for_product(product, db: Session):
    """
    Finds the best supplier match for a given product using smart logic
    """
    suppliers = db.query(models.Supplier).filter(
        models.Supplier.category == product.category
    ).all()
    
    if not suppliers:
        # Fallback to any supplier
        suppliers = db.query(models.Supplier).all()
    
    if not suppliers:
        return None
    
    # Score all suppliers
    supplier_scores = []
    for supplier in suppliers:
        score = calculate_supplier_score(supplier, product.unit_price)
        supplier_scores.append({
            "supplier": supplier,
            "score": score
        })
def generate_ai_morning_briefing(health_score, critical_count, pending_pos, db: Session):
    products = db.query(models.Product).all()
    critical_products = [p.name for p in products if p.current_stock < (p.optimal_stock_level * 0.2)][:2]
    
    if health_score < 60:
        status_text = "Supply chain health is highly critical."
    elif health_score < 80:
        status_text = "Supply chain health requires attention."
    else:
        status_text = "Supply chain operations are stable."
        
    critical_str = f" Immediate action needed on {', '.join(critical_products)}." if critical_products else ""
    return f"{status_text} Currently tracking {pending_pos} pending purchase orders. You have {critical_count} critical inventory items.{critical_str}"

def generate_urgency_reasoning(product, supplier, has_active_po=False, po_status=None):
    stock_pct = (product.current_stock / product.optimal_stock_level * 100) if product.optimal_stock_level > 0 else 0
    if has_active_po:
        verb = "Approved" if po_status == "APPROVED" else "In Transit" if po_status == "IN_TRANSIT" else "Drafted"
        return f"A Purchase Order is currently {verb}. Stock remains at {stock_pct:.0f}% pending delivery."
    if stock_pct < 20:
        return f"Stock critically low at {stock_pct:.0f}%. We recommend immediate replenishment from {supplier.name}."
    elif stock_pct < 35:
        return f"Stock dropping ({stock_pct:.0f}%). Consider ordering from {supplier.name} soon to avoid stockouts."
    else:
        return f"Stock is stable at {stock_pct:.0f}%."

@app.get("/procurement/health")
def get_procurement_health(db: Session = Depends(database.get_db)):
    """
    Returns comprehensive supply chain health metrics
    """
    health_score = calculate_supply_chain_health_score(db)
    
    products = db.query(models.Product).all()
    critical_count = sum(1 for p in products if p.current_stock < (p.optimal_stock_level * 0.2))
    
    pending_pos = db.query(models.PurchaseOrder).filter(
        models.PurchaseOrder.status.in_(["DRAFT", "APPROVED"])
    ).count()
    
    briefing = generate_ai_morning_briefing(health_score, critical_count, pending_pos, db)
    
    return {
        "health_score": round(health_score, 1),
        "critical_items_count": critical_count,
        "pending_pos": pending_pos,
        "morning_briefing": briefing,
        "status": "CRITICAL" if health_score < 60 else "WARNING" if health_score < 80 else "HEALTHY"
    }

@app.get("/procurement/recommendations")
def get_smart_recommendations(db: Session = Depends(database.get_db)):
    """
    Returns AI-powered procurement recommendations with matched suppliers
    """
    products = db.query(models.Product).all()
    
    # Identify products that need reordering
    critical_products = [
        p for p in products 
        if p.current_stock < (p.optimal_stock_level * 0.5)
    ]
    
    recommendations = []
    for product in critical_products[:10]:  # Limit to top 10
        # Find best supplier
        best_supplier = find_best_supplier_for_product(product, db)
        
        if not best_supplier:
            continue
        
        # Calculate urgency
        stock_pct = (product.current_stock / product.optimal_stock_level * 100) if product.optimal_stock_level > 0 else 0
        
        if stock_pct < 20:
            urgency = "CRITICAL"
            urgency_color = "#D32F2F"
        elif stock_pct < 35:
            urgency = "HIGH"
            urgency_color = "#F57C00"
        else:
            urgency = "MEDIUM"
            urgency_color = "#FBC02D"
        
        # Calculate quantity needed
        qty_needed = max(0, product.optimal_stock_level - product.current_stock)
        
        # Calculate estimated cost
        total_cost = qty_needed * product.unit_price
        
        # Generate AI reasoning
        reasoning = generate_urgency_reasoning(product, best_supplier)
        
        # Calculate supplier score
        supplier_score = calculate_supplier_score(best_supplier, product.unit_price)
        
        recommendations.append({
            "product_id": product.id,
            "product_name": product.name,
            "sku": product.sku,
            "current_stock": product.current_stock,
            "optimal_stock": product.optimal_stock_level,
            "stock_percentage": round(stock_pct, 1),
            "urgency": urgency,
            "urgency_color": urgency_color,
            "quantity_needed": qty_needed,
            "supplier_id": best_supplier.id,
            "supplier_name": best_supplier.name,
            "supplier_score": supplier_score,
            "delivery_days": best_supplier.delivery_speed_days,
            "estimated_cost": round(total_cost, 2),
            "ai_reasoning": reasoning
        })
    
    # Sort by urgency and stock percentage
    urgency_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}
    recommendations.sort(key=lambda x: (urgency_order[x["urgency"]], x["stock_percentage"]))
    
    return recommendations

@app.get("/procurement/suppliers/analysis")
def analyze_suppliers(db: Session = Depends(database.get_db)):
    """
    Returns detailed supplier performance analysis
    """
    suppliers = db.query(models.Supplier).all()
    
    analysis = []
    for supplier in suppliers:
        # Get PO history
        pos = db.query(models.PurchaseOrder).filter(
            models.PurchaseOrder.supplier_id == supplier.id
        ).all()
        
        total_pos = len(pos)
        completed_pos = len([p for p in pos if p.status == "RECEIVED"])
        
        # Calculate on-time delivery rate
        on_time_rate = (completed_pos / total_pos * 100) if total_pos > 0 else 0
        
        # AI verdict
        if supplier.reliability_score >= 90 and on_time_rate >= 85:
            verdict = "PREFERRED"
            verdict_color = "#2E7D32"
        elif supplier.reliability_score < 70 or on_time_rate < 60:
            verdict = "AT_RISK"
            verdict_color = "#C62828"
        else:
            verdict = "REVIEW_NEEDED"
            verdict_color = "#F57C00"
        
        # Calculate overall score
        overall_score = calculate_supplier_score(supplier)
        
        analysis.append({
            "id": supplier.id,
            "name": supplier.name,
            "category": supplier.category,
            "reliability_score": supplier.reliability_score,
            "delivery_speed_days": supplier.delivery_speed_days,
            "price_per_unit": supplier.price_per_unit,
            "total_pos": total_pos,
            "on_time_delivery_rate": round(on_time_rate, 1),
            "overall_score": overall_score,
            "verdict": verdict,
            "verdict_color": verdict_color
        })
    
    return analysis

@app.post("/procurement/suppliers/create")
def create_supplier(supplier: SupplierCreate, db: Session = Depends(database.get_db)):
    """
    Creates a new supplier with AI trust score calculation
    """
    # Check if supplier already exists
    existing = db.query(models.Supplier).filter(
        models.Supplier.name == supplier.name
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Supplier with this name already exists")
    
    # Create supplier
    db_supplier = models.Supplier(
        name=supplier.name,
        contact_email=supplier.contact_email,
        category=supplier.category,
        reliability_score=supplier.reliability_score,
        delivery_speed_days=supplier.delivery_speed_days,
        lead_time_days=supplier.delivery_speed_days,
        price_per_unit=supplier.price_per_unit
    )
    
    db.add(db_supplier)
    db.commit()
    db.refresh(db_supplier)
    
    # Calculate initial trust score
    trust_score = calculate_supplier_score(db_supplier)
    
    return {
        "message": "Supplier created successfully",
        "supplier_id": db_supplier.id,
        "initial_trust_score": trust_score
    }

@app.post("/procurement/po/create")
def create_purchase_order(po: POCreate, db: Session = Depends(database.get_db)):
    """
    Creates a new purchase order with smart defaults
    """
    # Validate supplier and product
    supplier = db.query(models.Supplier).filter(models.Supplier.id == po.supplier_id).first()
    product = db.query(models.Product).filter(models.Product.id == po.product_id).first()
    
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Generate PO number
    po_count = db.query(models.PurchaseOrder).count()
    po_number = f"PO-{datetime.now().strftime('%Y%m')}-{po_count + 1:04d}"
    
    # Calculate expected delivery
    expected_delivery = datetime.now() + timedelta(days=supplier.delivery_speed_days)
    
    # Calculate total value
    total_value = po.quantity * po.unit_price
    
    # Create PO
    db_po = models.PurchaseOrder(
        po_number=po_number,
        supplier_id=po.supplier_id,
        product_name=po.product_name,
        quantity=po.quantity,
        total_value=total_value,
        total_amount=total_value,
        priority=po.priority,
        status="DRAFT",
        expected_delivery=expected_delivery,
        expected_delivery_date=expected_delivery.date()
    )
    
    db.add(db_po)
    db.commit()
    db.refresh(db_po)
    
    # Create PO Item
    po_item = models.POItem(
        po_id=db_po.id,
        product_id=po.product_id,
        quantity_ordered=po.quantity,
        unit_price=po.unit_price
    )
    
    db.add(po_item)
    db.commit()
    
    return {
        "message": "Purchase order created",
        "po_number": po_number,
        "po_id": db_po.id,
        "expected_delivery": expected_delivery.strftime("%Y-%m-%d")
    }

@app.get("/procurement/po/list")
def list_purchase_orders(db: Session = Depends(database.get_db)):
    """
    Returns all purchase orders with enhanced details
    """
    pos = db.query(models.PurchaseOrder).all()
    
    result = []
    for po in pos:
        supplier = db.query(models.Supplier).filter(models.Supplier.id == po.supplier_id).first()
        
        # Calculate days until delivery
        if po.expected_delivery:
            days_remaining = (po.expected_delivery - datetime.now()).days
        else:
            days_remaining = 0
        
        # Status color
        status_colors = {
            "DRAFT": "#9E9E9E",
            "APPROVED": "#2196F3",
            "IN_TRANSIT": "#FF9800",
            "RECEIVED": "#4CAF50"
        }
        
        result.append({
            "id": po.id,
            "po_number": po.po_number,
            "supplier_name": supplier.name if supplier else "Unknown",
            "product_name": po.product_name,
            "quantity": po.quantity,
            "total_value": po.total_value,
            "status": po.status,
            "status_color": status_colors.get(po.status, "#757575"),
            "priority": po.priority,
            "expected_delivery": po.expected_delivery.strftime("%Y-%m-%d") if po.expected_delivery else "N/A",
            "days_remaining": days_remaining,
            "created_at": po.created_at.strftime("%Y-%m-%d") if po.created_at else "N/A"
        })
    
    return result

@app.put("/procurement/po/{po_id}/status")
def update_po_status(po_id: int, status: str, db: Session = Depends(database.get_db)):
    """
    Updates PO status and triggers stock update if received
    """
    valid_statuses = ["DRAFT", "APPROVED", "IN_TRANSIT", "RECEIVED"]
    
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    po = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.id == po_id).first()
    
    if not po:
        raise HTTPException(status_code=404, detail="PO not found")
    
    po.status = status
    
    # If status is RECEIVED, update product stock
    if status == "RECEIVED":
        po_items = db.query(models.POItem).filter(models.POItem.po_id == po_id).all()
        
        for item in po_items:
            product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
            if product:
                product.current_stock += item.quantity_ordered
                
                # Log the movement
                log = models.InventoryLog(
                    product_id=product.id,
                    quantity_change=item.quantity_ordered,
                    reason=f"PO Received: {po.po_number}",
                    change_date=datetime.utcnow()
                )
                db.add(log)
    
    db.commit()
    
    return {"message": "Status updated", "new_status": status}

@app.post("/procurement/draft_email")
def draft_negotiation_email(req: ReorderRequest):
    """
    Generates a professional negotiation email using AI
    """
    needed = max(0, req.optimal_stock - req.current_stock)
    if needed == 0:
        needed = 100
    
    cost = needed * req.unit_price
    
    prompt = f"""
    Write a professional procurement email for a Purchase Order.
    
    Details:
    - Supplier: {req.supplier_name}
    - Product: {req.product_name}
    - Quantity: {needed} units
    - Estimated Cost: ${cost:,.2f}
    - Urgency: Current stock is {req.current_stock}/{req.optimal_stock}
    
    Tone: Professional, polite, and emphasize partnership.
    Include: Subject line, greeting, body with PO details, and polite closing.
    Format as a real email.
    """
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        return {
            "email_draft": response.choices[0].message.content,
            "recommended_qty": needed,
            "estimated_cost": round(cost, 2)
        }
    except openai.RateLimitError:
        return {
            "email_draft": "AI Rate Limit Reached. Please use a manual template.",
            "recommended_qty": needed,
            "estimated_cost": round(cost, 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Email Failed: {str(e)}")

# --- EXISTING AI AGENTS ---
@app.post("/procurement/suppliers/{supplier_id}/negotiation_email")
def generate_supplier_negotiation_email(supplier_id: int, db: Session = Depends(database.get_db)):
    """
    Generate an AI-powered negotiation email for a specific supplier
    """
    # Get supplier details
    supplier = db.query(models.Supplier).filter(models.Supplier.id == supplier_id).first()
    
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Get recent POs with this supplier
    recent_pos = db.query(models.PurchaseOrder).filter(
        models.PurchaseOrder.supplier_id == supplier_id
    ).order_by(models.PurchaseOrder.created_at.desc()).limit(5).all()
    
    # Calculate total business volume
    total_volume = sum(po.total_value or 0 for po in recent_pos)
    po_count = len(recent_pos)
    
    # Generate context for AI
    prompt = f"""
    Write a professional procurement negotiation email to strengthen our partnership.
    
    Supplier Details:
    - Name: {supplier.name}
    - Contact: {supplier.contact_email}
    - Category: {supplier.category}
    - Current Reliability Score: {supplier.reliability_score}/100
    - Average Delivery Time: {supplier.delivery_speed_days} days
    - Current Price per Unit: ${supplier.price_per_unit}
    
    Our Business Relationship:
    - Total Purchase Orders: {po_count}
    - Total Business Volume: ${total_volume:,.2f}
    
    Email Goals:
    1. Acknowledge our strong partnership
    2. Discuss potential volume discounts (we're growing)
    3. Explore faster delivery options
    4. Request quarterly business review meeting
    
    Tone: Professional, collaborative, forward-thinking
    Include: Subject line, greeting, 3-4 paragraph body, call-to-action, professional closing
    
    Format as a complete email ready to send.
    """
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a professional procurement manager writing strategic supplier emails."},
                {"role": "user", "content": prompt}
            ]
        )
        
        email_content = response.choices[0].message.content
        
        return {
            "email": email_content,
            "supplier_name": supplier.name,
            "supplier_email": supplier.contact_email,
            "context": {
                "total_pos": po_count,
                "total_volume": round(total_volume, 2),
                "reliability": supplier.reliability_score
            }
        }
    except openai.RateLimitError:
        return {
            "email": "AI Rate Limit Reached. Please draft this negotiation email manually.",
            "supplier_name": supplier.name,
            "supplier_email": supplier.contact_email,
            "context": {
                "total_pos": po_count,
                "total_volume": round(total_volume, 2),
                "reliability": supplier.reliability_score
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Email Generation Failed: {str(e)}")


def _build_procurement_supplier_analysis(db: Session):
    suppliers = db.query(models.Supplier).all()
    analysis = []

    for supplier in suppliers:
        pos = db.query(models.PurchaseOrder).filter(
            models.PurchaseOrder.supplier_id == supplier.id
        ).all()

        total_pos = len(pos)
        completed_pos = len([po for po in pos if po.status == "RECEIVED"])
        on_time_rate = round((completed_pos / total_pos * 100), 1) if total_pos else 0.0
        overall_score = calculate_supplier_score(supplier)

        if supplier.reliability_score >= 90 and on_time_rate >= 85:
            verdict = "Partner"
        elif supplier.reliability_score < 70 or on_time_rate < 60:
            verdict = "At Risk"
        else:
            verdict = "Vetted"

        quality_proxy = round(
            min(100.0, ((supplier.reliability_score or 0) * 0.7) + (on_time_rate * 0.3)),
            1,
        )

        analysis.append({
            "id": str(supplier.id),
            "name": supplier.name,
            "location": supplier.category or "Location pending",
            "verdict": verdict,
            "score": overall_score,
            "reliability": round(supplier.reliability_score or 0, 1),
            "onTimeDelivery": on_time_rate,
            "qualityRate": quality_proxy,
            "deliverySpeedDays": supplier.delivery_speed_days,
            "pricePerUnit": round(supplier.price_per_unit or 0, 2),
        })

    return analysis


def _build_procurement_insights(db: Session, limit: int = 10):
    products = db.query(models.Product).all()
    insights = []

    for product in products:
        if product.optimal_stock_level <= 0:
            continue

        best_supplier = find_best_supplier_for_product(product, db)
        if not best_supplier:
            continue

        # Get POs associated with this product
        active_pos = db.query(models.PurchaseOrder).join(models.POItem).filter(
            models.POItem.product_id == product.id,
            models.PurchaseOrder.status.in_(["DRAFT", "APPROVED", "IN_TRANSIT"])
        ).order_by(models.PurchaseOrder.created_at.desc()).all()
        
        has_active_po = len(active_pos) > 0
        latest_po = active_pos[0] if has_active_po else None
        
        incoming_qty = sum(item.quantity_ordered for po in active_pos for item in po.items if item.product_id == product.id)
        effective_stock_pct = ((product.current_stock + incoming_qty) / product.optimal_stock_level * 100)
        stock_pct = (product.current_stock / product.optimal_stock_level * 100)
        
        if effective_stock_pct >= 60 and not has_active_po:
            continue # Already sufficiently stocked
            
        if effective_stock_pct < 20:
            priority = "urgent"
        elif effective_stock_pct < 35:
            priority = "high"
        else:
            priority = "monitor"

        if has_active_po:
            statusstr = latest_po.status
            if statusstr == "DRAFT":
                action_label = "PO Drafted"
            elif statusstr == "APPROVED":
                action_label = "PO Approved"
            elif statusstr == "IN_TRANSIT":
                action_label = "In Transit"
            else:
                action_label = "PO Active"
            action_type = "view_po"
        else:
            if priority in ["urgent", "high"]:
                action_label = "Quick PO"
                action_type = "quick_po"
            else:
                action_label = "Draft Email"
                action_type = "draft_email"

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
            "id": str(product.id),
            "productId": product.id,
            "supplierId": best_supplier.id,
            "sku": product.sku,
            "title": product.name,
            "priority": priority,
            "reasoning": reasoning,
            "unitPrice": supplier_unit_price,
            "supplierScore": supplier_score,
            "estimatedLeadTime": f"{best_supplier.delivery_speed_days} Days",
            "estimatedLeadTimeDays": best_supplier.delivery_speed_days,
            "replenishmentQty": replenishment_qty,
            "actionLabel": action_label,
            "actionType": action_type,
            "supplierName": best_supplier.name,
            "estimatedCost": estimated_cost,
        })

    priority_order = {"urgent": 0, "high": 1, "monitor": 2, "normal": 3}
    insights.sort(key=lambda item: (priority_order[item["priority"]], item["estimatedLeadTimeDays"]))
    return insights[:limit]


@app.get("/api/procurement/summary")
def get_procurement_summary(db: Session = Depends(database.get_db)):
    health_score = calculate_supply_chain_health_score(db)
    products = db.query(models.Product).all()
    suppliers = db.query(models.Supplier).all()
    
    # Calculate pending correctly
    pending_pos = db.query(models.PurchaseOrder).filter(
        models.PurchaseOrder.status == "DRAFT"
    ).count()
    approved_pos = db.query(models.PurchaseOrder).filter(
        models.PurchaseOrder.status.in_(["APPROVED", "IN_TRANSIT"])
    ).count()

    # Calculate critical items accounting for expected deliveries
    critical_items = 0
    for product in products:
        incoming_qty = sum(item.quantity_ordered for item in product.po_items if item.purchase_order and item.purchase_order.status in ["DRAFT", "APPROVED", "IN_TRANSIT"])
        if (product.current_stock + incoming_qty) < (product.optimal_stock_level * 0.2):
            critical_items += 1

    insights = _build_procurement_insights(db, limit=12)

    product_lookup = {product.id: product for product in products}
    savings_to_date = round(
        sum(
            max(0, (product_lookup[insight["productId"]].unit_price or 0) - insight["unitPrice"]) * insight["replenishmentQty"]
            for insight in insights
            if insight["productId"] in product_lookup and insight["actionType"] == "quick_po"
        ),
        2,
    )

    avg_supplier_lead = (
        round(sum(s.delivery_speed_days or 0 for s in suppliers) / len(suppliers))
        if suppliers
        else 0
    )
    fastest_lead = min((s.delivery_speed_days or 0 for s in suppliers), default=avg_supplier_lead)
    lead_opportunity = max(avg_supplier_lead - fastest_lead, 0)
    projected_spend = sum(insight["estimatedCost"] for insight in insights if insight["actionType"] == "quick_po")
    savings_pct = round((savings_to_date / max(projected_spend, 1)) * 100, 1)

    status = "optimal" if health_score >= 80 else "warning" if health_score >= 60 else "critical"

    return {
        "systemHealthScore": round(health_score),
        "healthStatus": status,
        "aiBriefing": generate_ai_morning_briefing(health_score, critical_items, pending_pos, db),
        "criticalItems": critical_items,
        "pendingPOs": pending_pos,
        "savingsToDate": savings_to_date,
        "savingsChange": f"+{savings_pct}% projected",
        "leadTimeAverage": f"{avg_supplier_lead}d",
        "leadTimeChange": f"-{lead_opportunity}d opportunity" if lead_opportunity else "Stable lead time",
    }


@app.get("/api/procurement/insights")
def get_procurement_insights(priority: Optional[str] = None, db: Session = Depends(database.get_db)):
    insights = _build_procurement_insights(db, limit=12)
    if priority and priority.lower() != "all":
        insights = [insight for insight in insights if insight["priority"] == priority.lower()]
    return insights


@app.get("/api/procurement/suppliers/overview")
def get_procurement_suppliers_overview(db: Session = Depends(database.get_db)):
    analysis = _build_procurement_supplier_analysis(db)

    avg_reliability = round(sum(item["reliability"] for item in analysis) / len(analysis), 1) if analysis else 0.0
    on_time_delivery = round(sum(item["onTimeDelivery"] for item in analysis) / len(analysis), 1) if analysis else 0.0
    quality_rate = round(sum(item["qualityRate"] for item in analysis) / len(analysis), 1) if analysis else 0.0
    average_score = round(sum(item["score"] for item in analysis) / len(analysis), 1) if analysis else 0.0

    if average_score >= 95:
        esg_compliance = "A+"
    elif average_score >= 90:
        esg_compliance = "A"
    elif average_score >= 80:
        esg_compliance = "B+"
    else:
        esg_compliance = "B"

    return {
        "overview": {
            "avgReliability": avg_reliability,
            "onTimeDelivery": on_time_delivery,
            "qualityRate": quality_rate,
            "esgCompliance": esg_compliance,
        },
        "suppliers": analysis,
    }


@app.get("/api/procurement/suppliers/top-performers")
def get_procurement_top_performers(db: Session = Depends(database.get_db)):
    analysis = sorted(_build_procurement_supplier_analysis(db), key=lambda item: item["score"], reverse=True)[:3]

    performers = []
    for index, supplier in enumerate(analysis, start=1):
        metric_label = (
            f"{supplier['qualityRate']}% Quality"
            if index == 1
            else f"{supplier['onTimeDelivery']}% On-time"
            if index == 2
            else f"{supplier['reliability']}% Reliability"
        )
        performers.append({
            "id": supplier["id"],
            "rank": index,
            "name": supplier["name"],
            "metricLabel": metric_label,
            "score": supplier["score"],
        })

    return performers


@app.get("/api/procurement/spend-optimization")
def get_procurement_spend_optimization(db: Session = Depends(database.get_db)):
    insights = _build_procurement_insights(db, limit=20)
    product_lookup = {product.id: product for product in db.query(models.Product).all()}

    baseline_spend = 0.0
    optimized_spend = 0.0
    for insight in insights:
        product = product_lookup.get(insight["productId"])
        if not product:
            continue
        baseline_spend += insight["replenishmentQty"] * (product.unit_price or 0)
        optimized_spend += insight["estimatedCost"]

    total_value = round(max(0, baseline_spend - optimized_spend), 2)
    budget_pool = optimized_spend + max(total_value * 4, optimized_spend * 0.2, 1)
    budget_utilization = round((optimized_spend / budget_pool) * 100, 1) if budget_pool else 0.0

    return {
        "totalValue": total_value,
        "yoyChange": f"+{round((total_value / max(baseline_spend, 1)) * 100, 1)}% projected",
        "budgetUtilization": budget_utilization,
        "buttonLabel": "Download Report",
    }


@app.get("/api/procurement/purchase-orders")
def get_procurement_purchase_orders(
    limit: Optional[int] = None,
    page: int = 1,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    supplier: Optional[str] = None,
    search: Optional[str] = None,
    date_range: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sort: str = "latest",
    db: Session = Depends(database.get_db),
):
    query = db.query(models.PurchaseOrder)
    supplier_joined = False

    if status:
        normalized_status = status.strip().replace(" ", "_").upper()
        query = query.filter(models.PurchaseOrder.status == normalized_status)

    if priority:
        normalized_priority = priority.strip().lower()
        query = query.filter(func.lower(models.PurchaseOrder.priority) == normalized_priority)

    if supplier:
        supplier_joined = True
        query = query.join(models.Supplier).filter(func.lower(models.Supplier.name) == supplier.strip().lower())

    if search:
        pattern = f"%{search.strip().lower()}%"
        if not supplier_joined:
            query = query.join(models.Supplier, isouter=True)
        query = query.filter(
            func.lower(models.PurchaseOrder.po_number).like(pattern)
            | func.lower(func.coalesce(models.PurchaseOrder.product_name, "")).like(pattern)
            | func.lower(func.coalesce(models.Supplier.name, "")).like(pattern)
        )

    now_utc = datetime.utcnow()
    if date_range:
        range_key = date_range.strip().lower()
        if range_key == "today":
            start_dt = datetime.combine(now_utc.date(), datetime.min.time())
            query = query.filter(models.PurchaseOrder.created_at >= start_dt)
        elif range_key in {"7d", "30d"}:
            days = 7 if range_key == "7d" else 30
            query = query.filter(models.PurchaseOrder.created_at >= (now_utc - timedelta(days=days)))

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid start_date format") from exc
        query = query.filter(models.PurchaseOrder.created_at >= start_dt)

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid end_date format") from exc
        query = query.filter(models.PurchaseOrder.created_at <= end_dt + timedelta(days=1))

    if sort == "oldest":
        query = query.order_by(models.PurchaseOrder.created_at.asc())
    else:
        query = query.order_by(models.PurchaseOrder.created_at.desc())

    if limit is not None:
        safe_limit = max(1, min(limit, 100))
        safe_page = max(page, 1)
        query = query.offset((safe_page - 1) * safe_limit).limit(safe_limit)
    pos = query.all()
    lifecycle_order = {
        "DRAFT": "draft",
        "APPROVED": "approved",
        "IN_TRANSIT": "in_transit",
        "RECEIVED": "received",
    }

    results = []
    for po in pos:
        supplier = db.query(models.Supplier).filter(models.Supplier.id == po.supplier_id).first()
        results.append({
            "id": str(po.id),
            "poNumber": po.po_number,
            "title": po.product_name or "Procurement item",
            "supplierName": supplier.name if supplier else "Unknown supplier",
            "status": (po.status or "DRAFT").replace("_", " ").title(),
            "priority": (po.priority or "Medium").title(),
            "lifecycleStage": lifecycle_order.get(po.status or "DRAFT", "draft"),
            "createdAt": po.created_at.isoformat() if po.created_at else None,
            "expectedDelivery": po.expected_delivery.isoformat() if po.expected_delivery else None,
        })

    return results


@app.post("/api/procurement/purchase-orders/create")
def create_procurement_purchase_order(payload: QuickPOCreate, db: Session = Depends(database.get_db)):
    product, supplier = _resolve_procurement_context(payload, db)
    db_po = _create_purchase_order_record(
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
        "status": _normalize_purchase_order_status(db_po.status),
        "createdAt": created_at.isoformat(),
        "previewUrl": f"/api/procurement/purchase-orders/{db_po.id}",
    }


@app.get("/api/procurement/purchase-orders/{po_id}")
def get_procurement_purchase_order(po_id: int, db: Session = Depends(database.get_db)):
    db_po = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.id == po_id).first()
    if not db_po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return _build_purchase_order_document(db_po, db)


@app.put("/api/procurement/purchase-orders/{po_id}/status")
def update_procurement_purchase_order_status(
    po_id: int,
    payload: POStatusUpdate,
    db: Session = Depends(database.get_db),
):
    status = (payload.status or "").strip().upper()
    valid_statuses = ["DRAFT", "APPROVED", "IN_TRANSIT", "RECEIVED"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid purchase order status")

    db_po = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.id == po_id).first()
    if not db_po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    db_po.status = status
    db.commit()
    db.refresh(db_po)
    return _build_purchase_order_document(db_po, db)


@app.get("/api/procurement/purchase-orders/{po_id}/pdf")
def download_procurement_purchase_order_pdf(po_id: int, db: Session = Depends(database.get_db)):
    db_po = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.id == po_id).first()
    if not db_po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    document = _build_purchase_order_document(db_po, db)
    pdf_bytes = _build_purchase_order_pdf(document)
    filename = f"{document['poNumber']}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

@app.post("/ai/pricing_analysis")
def analyze_pricing_strategy(req: PricingRequest):
    ratio = req.current_stock / req.optimal_stock if req.optimal_stock > 0 else 0
    
    prompt = f"""
    You are a Strategic Pricing Algorithm.
    
    DATA:
    - Product: {req.product_name}
    - Current Price: ${req.current_price}
    - Stock Ratio: {ratio:.2f}
    
    RULES:
    1. IF Ratio > 1.5: LOWER price
    2. IF Ratio < 0.3: RAISE price
    3. ELSE: HOLD price
    
    OUTPUT JSON:
    {{
        "new_price": float,
        "action": "RAISE/LOWER/HOLD",
        "reason": "string",
        "confidence": 95
    }}
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Output strict JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except openai.RateLimitError:
        return {
            "new_price": req.current_price,
            "action": "HOLD",
            "reason": "AI currently rate limited. No automated pricing action taken.",
            "confidence": 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Pricing Failed: {str(e)}")

@app.post("/ai/parse_product_info")
def parse_product_info(request: AIProductParseRequest):
    # Validate input
    if not request.description or request.description.strip() == "":
        raise HTTPException(status_code=400, detail="Description cannot be empty")
    
    prompt = f"""
    Extract product details from: "{request.description}"
    
    Output JSON:
    {{
        "name": "...",
        "category": "...",
        "stage": "...",
        "current_stock": 0,
        "unit_price": 0.0,
        "optimal_stock_level": 0,
        "safety_stock_level": 0
    }}
    """
    try:
        if not GROQ_API_KEY:
            return parse_product_info_local(request.description)
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Output JSON only."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        # Parse the JSON response
        result = json.loads(response.choices[0].message.content)
        return result
        
    except json.JSONDecodeError as e:
        return parse_product_info_local(request.description)
    except openai.RateLimitError:
        return parse_product_info_local(request.description)
    except Exception as e:
        traceback.print_exc()
        return parse_product_info_local(request.description)

@app.post("/ai/audit_inventory")
def audit_inventory(req: InventoryReportRequest):
    data_summary = "\n".join([f"- {p['product']}: Stock {p['on_hand']}/{p['optimal_stock']}" for p in req.products])
    prompt = f"""
    Supply Chain CFO Audit. Inventory: {data_summary}
    Write Strategic Report (Markdown): Executive Summary, Risks, Recommendations.
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        return {"report": response.choices[0].message.content}
    except openai.RateLimitError:
        return {"report": "AI Rate Limit Reached. Strategic audit is temporarily unavailable."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audit Failed: {str(e)}")

@app.post("/ai/simulate_scenario")
def simulate_scenario(req: SimulationRequest):
    context = "\n".join([f"- {p['product']}: Stock {p['on_hand']}" for p in req.products])
    prompt = f"""
    Risk Analyst. Inventory: {context}. Scenario: "{req.scenario}"
    Output JSON: impact_score, impact_summary, affected_products, recommendation.
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "JSON only."}, {"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except openai.RateLimitError:
        return {
            "impact_score": 50,
            "impact_summary": "AI Rate Limit Reached. Simulation unavailable.",
            "affected_products": [],
            "recommendation": "Monitor inventory levels manually."
        }
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/ai/generate_reorder_email")
def generate_reorder_email(req: ReorderRequest):
    return draft_negotiation_email(req)

@app.post("/ai/agent/route")
def agent_route(req: AgentRouteRequest):
    return SupplyChainAgent.route(req.intent, req.payload)

# --- INVENTORY CRUD ---

@app.post("/products/")
def create_product(product: ProductCreate, db: Session = Depends(database.get_db)):
    existing = db.query(models.Product).filter(models.Product.sku == product.sku).first()
    if existing:
        raise HTTPException(status_code=400, detail="SKU exists")
    db_product = models.Product(**product.dict())
    db.add(db_product)
    db.commit()
    return {"message": "Created", "id": db_product.id}

@app.put("/products/{product_id}")
def update_product(product_id: int, product: ProductUpdate, db: Session = Depends(database.get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if product.stage:
        db_product.stage = product.stage
    if product.current_stock is not None:
        db_product.current_stock = product.current_stock
    if product.unit_price is not None:
        db_product.unit_price = product.unit_price
    if product.category:
        db_product.category = product.category
    
    db.commit()
    return {"message": "Updated"}

@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(database.get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(db_product)
    db.commit()
    return {"message": "Product deleted"}

@app.post("/inventory/logs")
def log_stock_movement(movement: StockMovement, db: Session = Depends(database.get_db)):
    product = db.query(models.Product).filter(models.Product.id == movement.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.current_stock += movement.quantity_change
    db_log = models.InventoryLog(
        product_id=movement.product_id,
        quantity_change=movement.quantity_change,
        reason=movement.reason,
        change_date=datetime.utcnow()
    )
    db.add(db_log)
    db.commit()
    return {"message": "Stock updated", "new_stock": product.current_stock}

@app.get("/inventory/analysis")
def analyze_inventory(db: Session = Depends(database.get_db)):
    products = db.query(models.Product).all()
    results = []
    for p in products:
        status = "OK"
        rec = "Optimal"
        if p.current_stock < p.safety_stock_level:
            status = "CRITICAL"
            rec = "Replenish immediately."
        elif p.current_stock < (p.safety_stock_level * 1.2):
            status = "LOW"
            rec = "Plan Reorder soon."
        
        results.append({
            "id": p.id,
            "product": p.name,
            "sku": p.sku,
            "on_hand": p.current_stock,
            "safety_stock": p.safety_stock_level,
            "optimal_stock": p.optimal_stock_level,
            "unit_price": p.unit_price,
            "category": p.category,
            "stage": p.stage,
            "status": status,
            "ai_recommendation": rec
        })
    return results

# --- ORDERS ---

@app.post("/orders/", response_model=OrderResponse)
def create_order(order: OrderCreate, db: Session = Depends(database.get_db)):
    risk = analyze_order_with_groq(order.delivery_address)
    db_order = models.Order(**order.dict(), status="PENDING", ai_risk_assessment=risk)
    db.add(db_order)
    db.commit()
    return db_order

@app.get("/orders/", response_model=List[OrderResponse])
def read_orders(db: Session = Depends(database.get_db)):
    return db.query(models.Order).all()

# --- FORECASTING,
def str_to_bool(value: str) -> bool:
    """Convert string to boolean"""
    if isinstance(value, bool):
        return value
    return str(value).lower() in ('true', '1', 'yes', 'on')


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "message": "Supply Chain AI System is Online 🚀",
        "features": [
            "Dynamic forecast horizon validation",
            "Multi-country support",
            "External factors analysis",
            "Seasonal pattern detection",
            "AI-powered insights"
        ]
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "min_months_required": settings.min_months_for_analysis,
        "recommended_months": settings.min_months_for_seasonality,
        "optimal_months": settings.optimal_months,
        "ai_model": settings.gemini_model,
        "max_forecast_horizon": settings.max_forecast_horizon,
        "supported_countries": ["IN", "US", "UK"]
    }


def _shipment_status_tone(status: str) -> str:
    return {
        "IN_TRANSIT": "primary",
        "SCHEDULED": "neutral",
        "DELAYED": "warning",
        "DELIVERED": "success",
    }.get(status, "neutral")


def _activity_timestamp(value) -> str:
    if not value:
        return datetime.utcnow().isoformat()
    return value.isoformat()


def _collect_dashboard_activities(db: Session, limit: int = 8):
    activities = []

    inventory_logs = (
        db.query(models.InventoryLog)
        .order_by(models.InventoryLog.change_date.desc())
        .limit(limit)
        .all()
    )
    for log in inventory_logs:
        product = db.query(models.Product).filter(models.Product.id == log.product_id).first()
        product_name = product.name if product else f"Product #{log.product_id}"
        qty = abs(log.quantity_change or 0)
        action = "added" if (log.quantity_change or 0) >= 0 else "removed"
        reason = (log.reason or "stock update").replace("_", " ").title()
        activities.append({
            "id": f"inventory-{log.id}",
            "title": f"{product_name} stock updated",
            "description": f"{qty} units {action} via {reason}",
            "timestamp": _activity_timestamp(log.change_date),
            "type": "inventory",
        })

    purchase_orders = (
        db.query(models.PurchaseOrder)
        .order_by(models.PurchaseOrder.created_at.desc())
        .limit(limit)
        .all()
    )
    for po in purchase_orders:
        supplier_name = po.supplier.name if po.supplier else "Unknown supplier"
        status_label = (po.status or "DRAFT").replace("_", " ").title()
        qty = po.quantity or 0
        product_name = po.product_name or "inventory"
        activities.append({
            "id": f"po-{po.id}",
            "title": f"PO {po.po_number} {status_label.lower()}",
            "description": f"{qty} units of {product_name} with {supplier_name}",
            "timestamp": _activity_timestamp(po.created_at),
            "type": "procurement",
        })

    shipments = (
        db.query(models.Shipment)
        .order_by(models.Shipment.created_at.desc())
        .limit(limit)
        .all()
    )
    for shipment in shipments:
        status_label = (shipment.status or "SCHEDULED").replace("_", " ").title()
        progress = round(shipment.progress_percent or 0)
        activities.append({
            "id": f"shipment-{shipment.id}",
            "title": f"Shipment {shipment.tracking_number} {status_label.lower()}",
            "description": f"{shipment.origin} to {shipment.destination} at {progress}% completion",
            "timestamp": _activity_timestamp(shipment.created_at),
            "type": "shipment",
        })

    orders = (
        db.query(models.Order)
        .order_by(models.Order.created_at.desc())
        .limit(limit)
        .all()
    )
    for order in orders:
        status_label = (order.status or "PENDING").replace("_", " ").title()
        activities.append({
            "id": f"order-{order.id}",
            "title": f"Order #{order.id} {status_label.lower()}",
            "description": f"{order.customer_name} delivery to {order.delivery_address or 'address pending'}",
            "timestamp": _activity_timestamp(order.created_at),
            "type": "order",
        })

    activities.sort(key=lambda item: item["timestamp"], reverse=True)
    return activities[:limit]


@app.get("/api/dashboard/metrics")
def get_dashboard_metrics(db: Session = Depends(database.get_db)):
    products = db.query(models.Product).all()
    purchase_orders = db.query(models.PurchaseOrder).all()

    total_skus = len(products)
    categories = len({product.category for product in products if product.category})
    critical_stock = sum(
        1 for product in products
        if (product.current_stock or 0) < (product.safety_stock_level or 0)
    )
    low_stock = sum(
        1 for product in products
        if (product.current_stock or 0) >= (product.safety_stock_level or 0)
        and (product.current_stock or 0) < ((product.safety_stock_level or 0) * 1.2)
    )
    active_pos = sum(1 for po in purchase_orders if po.status != "RECEIVED")
    in_transit_pos = sum(1 for po in purchase_orders if po.status == "IN_TRANSIT")
    inventory_value = round(
        sum((product.current_stock or 0) * (product.unit_price or 0) for product in products),
        2,
    )

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
            "value": inventory_value,
            "status": "Tracked inventory",
            "change": f"{total_skus} items valued live",
            "tone": "success",
            "icon": "payments",
            "format": "currency",
        },
    ]


@app.get("/api/dashboard/shipments")
def get_dashboard_shipments(db: Session = Depends(database.get_db)):
    shipments = (
        db.query(models.Shipment)
        .order_by(models.Shipment.created_at.desc())
        .limit(12)
        .all()
    )

    results = []
    for shipment in shipments:
        status = shipment.status or "SCHEDULED"
        status_label = status.replace("_", " ").title()
        progress = round(shipment.progress_percent or 0)
        if status == "DELAYED":
            detail = "Requires attention from logistics team"
        elif status == "DELIVERED":
            detail = "Completed and closed"
        elif status == "IN_TRANSIT":
            detail = "Carrier en route"
        else:
            detail = "Awaiting dispatch"

        results.append({
            "id": str(shipment.id),
            "trackingNumber": shipment.tracking_number,
            "source": shipment.origin,
            "destination": shipment.destination,
            "status": status_label,
            "progress": progress,
            "eta": shipment.eta.isoformat() if shipment.eta else None,
            "detail": detail,
            "tone": _shipment_status_tone(status),
        })

    return results


@app.get("/api/dashboard/activities")
def get_dashboard_activities(db: Session = Depends(database.get_db)):
    return _collect_dashboard_activities(db)


@app.get("/api/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(database.get_db)):
    raw_material_products = (
        db.query(models.Product)
        .filter(func.lower(models.Product.stage) == "raw material")
        .all()
    )
    raw_material_units = sum(product.current_stock or 0 for product in raw_material_products)

    active_shipments = (
        db.query(models.Shipment)
        .filter(models.Shipment.status.in_(["SCHEDULED", "IN_TRANSIT", "DELAYED"]))
        .all()
    )
    average_progress = (
        round(sum(shipment.progress_percent or 0 for shipment in active_shipments) / len(active_shipments), 1)
        if active_shipments
        else 0.0
    )

    active_carriers = (
        db.query(models.Shipment.carrier_id)
        .filter(models.Shipment.carrier_id.isnot(None))
        .distinct()
        .count()
    )
    total_carriers = db.query(models.Carrier).count()

    return [
        {
            "id": "raw-material",
            "label": "Raw Material Stock",
            "value": f"{raw_material_units:,} units",
            "description": f"{len(raw_material_products)} raw material SKUs",
            "icon": "inventory",
        },
        {
            "id": "delivery-progress",
            "label": "Avg. Delivery Progress",
            "value": f"{average_progress}%",
            "description": f"{len(active_shipments)} active routes",
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


@app.get("/api/dashboard/overview")
def get_dashboard_overview(db: Session = Depends(database.get_db)):
    products = db.query(models.Product).all()
    shipments = db.query(models.Shipment).all()
    orders = db.query(models.Order).all()
    purchase_orders = db.query(models.PurchaseOrder).all()

    inventory_status_counts = {"Healthy": 0, "Low": 0, "Critical": 0}
    inventory_stage_counts = {}
    product_value_rows = []

    for product in products:
        current_stock = product.current_stock or 0
        safety_stock = product.safety_stock_level or 0
        if current_stock < safety_stock:
            inventory_status = "Critical"
        elif current_stock < (safety_stock * 1.2):
            inventory_status = "Low"
        else:
            inventory_status = "Healthy"

        inventory_status_counts[inventory_status] += 1
        stage = product.stage or "Unknown"
        inventory_stage_counts[stage] = inventory_stage_counts.get(stage, 0) + 1

        inventory_value = round(current_stock * (product.unit_price or 0), 2)
        product_value_rows.append({
            "id": str(product.id),
            "name": product.name,
            "sku": product.sku,
            "category": product.category,
            "value": inventory_value,
            "stock": current_stock,
            "status": inventory_status,
        })

    shipment_status_counts = {}
    for shipment in shipments:
        status = (shipment.status or "SCHEDULED").replace("_", " ").title()
        shipment_status_counts[status] = shipment_status_counts.get(status, 0) + 1

    order_status_counts = {}
    for order in orders:
        status = (order.status or "PENDING").replace("_", " ").title()
        order_status_counts[status] = order_status_counts.get(status, 0) + 1

    po_status_counts = {}
    for po in purchase_orders:
        status = (po.status or "DRAFT").replace("_", " ").title()
        po_status_counts[status] = po_status_counts.get(status, 0) + 1

    top_inventory = sorted(product_value_rows, key=lambda item: item["value"], reverse=True)[:5]
    critical_products = [item for item in product_value_rows if item["status"] == "Critical"]
    delayed_shipments = [shipment for shipment in shipments if (shipment.status or "").upper() == "DELAYED"]
    pending_orders = [order for order in orders if (order.status or "").upper() == "PENDING"]

    executive_briefs = [
        {
            "id": "critical-stock",
            "title": "Critical replenishment pressure",
            "description": f"{len(critical_products)} SKUs are below safety stock and need procurement attention.",
            "tone": "danger" if critical_products else "success",
        },
        {
            "id": "shipment-risk",
            "title": "Logistics watchlist",
            "description": f"{len(delayed_shipments)} shipments are currently delayed across the network.",
            "tone": "warning" if delayed_shipments else "success",
        },
        {
            "id": "order-backlog",
            "title": "Demand backlog",
            "description": f"{len(pending_orders)} customer orders remain pending fulfillment.",
            "tone": "neutral" if pending_orders else "success",
        },
    ]

    return {
        "inventoryStatus": [
            {"id": "healthy", "label": "Healthy", "value": inventory_status_counts["Healthy"], "tone": "success"},
            {"id": "low", "label": "Low", "value": inventory_status_counts["Low"], "tone": "warning"},
            {"id": "critical", "label": "Critical", "value": inventory_status_counts["Critical"], "tone": "danger"},
        ],
        "inventoryStages": [
            {
                "id": stage.lower().replace(" ", "-"),
                "label": stage,
                "value": count,
                "tone": "primary",
            }
            for stage, count in sorted(inventory_stage_counts.items(), key=lambda item: item[1], reverse=True)
        ],
        "shipmentStatus": [
            {
                "id": label.lower().replace(" ", "-"),
                "label": label,
                "value": value,
                "tone": "warning" if label == "Delayed" else "primary",
            }
            for label, value in sorted(shipment_status_counts.items(), key=lambda item: item[1], reverse=True)
        ],
        "orderStatus": [
            {
                "id": label.lower().replace(" ", "-"),
                "label": label,
                "value": value,
                "tone": "neutral",
            }
            for label, value in sorted(order_status_counts.items(), key=lambda item: item[1], reverse=True)
        ],
        "purchaseOrderStatus": [
            {
                "id": label.lower().replace(" ", "-"),
                "label": label,
                "value": value,
                "tone": "neutral",
            }
            for label, value in sorted(po_status_counts.items(), key=lambda item: item[1], reverse=True)
        ],
        "topInventory": top_inventory,
        "executiveBriefs": executive_briefs,
    }


@app.post("/validate-data")
async def validate_data(
    file: UploadFile,
    category: str = Form(...),
    date_col: str = Form(...),
    category_col: str = Form(...),
    units_col: str = Form(...)
):
    """
    Validate uploaded data and return horizon availability.
    """
    try:
        # Read file
        contents = await file.read()
        
        # Try to parse CSV
        try:
            df = pd.read_csv(io.BytesIO(contents))
        except Exception as csv_error:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to read CSV file. Please ensure it's a valid CSV format. Error: {str(csv_error)}"
            )
        
        # Check if dataframe is empty
        if df.empty:
            raise HTTPException(
                status_code=400,
                detail="The uploaded CSV file is empty. Please upload a file with data."
            )
        
        # Validate columns exist
        missing_cols = []
        for col, name in [(date_col, "Date"), (category_col, "Category"), (units_col, "Units")]:
            if col not in df.columns:
                missing_cols.append(f"{name} column '{col}'")
        
        if missing_cols:
            raise HTTPException(
                status_code=400,
                detail=f"Missing columns: {', '.join(missing_cols)}. Available columns: {', '.join(df.columns.tolist())}"
            )
        
        # Prepare data
        try:
            monthly_df = prepare_category_data(
                df=df,
                category=category,
                date_col=date_col,
                category_col=category_col,
                units_col=units_col
            )
        except ValueError as ve:
            raise HTTPException(
                status_code=400,
                detail=str(ve)
            )
        
        data_months = len(monthly_df)
        data_summary = get_data_summary(monthly_df)
        
        # Validate each horizon
        horizon_validation = {}
        for horizon in [1, 3, 6]:
            validation = validate_forecast_horizon(data_months, horizon)
            horizon_validation[f"{horizon}_month"] = {
                "allowed": validation["valid"],
                "message": validation["message"],
                "confidence": validation["confidence"]
            }
        
        available_horizons = [h for h in [1, 3, 6] if horizon_validation[f"{h}_month"]["allowed"]]
        ready_for_forecast = data_months >= settings.min_months_for_analysis
        
        return {
            "status": "success",
            "category": category,
            "data_summary": data_summary,
            "horizon_validation": horizon_validation,
            "available_horizons": available_horizons,
            "ready_for_forecast": ready_for_forecast,
            "readiness_message": (
                "✅ Data is sufficient for forecasting" 
                if ready_for_forecast 
                else f"❌ Insufficient data. Need {settings.min_months_for_analysis} months minimum, have {data_months}"
            )
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # Log the full error for debugging
        print(f"Validation Error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500, 
            detail=f"Server error during validation: {str(e)}"
        )


@app.post("/forecast/upload")
async def upload_and_forecast(
    file: UploadFile,
    category: str = Form(...),
    date_col: str = Form(...),
    category_col: str = Form(...),
    units_col: str = Form(...),
    horizon: int = Form(1),
    # External factors
    upcoming_promotion: str = Form("false"),
    marketing_campaign: str = Form("false"),
    new_product_launch: str = Form("false"),
    availability_issues: str = Form("false"),
    price_change: str = Form("Same"),
    supply_chain_disruption: str = Form("false"),
    regulatory_changes: str = Form("false"),
    logistics_constraints: str = Form("false"),
    economic_uncertainty: str = Form("None"),
    region: str = Form("India"),
    country: str = Form("IN")
):
    """
    Upload sales data and generate adaptive AI-powered demand forecast.
    """
    
    try:
        # Validate horizon
        if horizon < 1 or horizon > settings.max_forecast_horizon:
            raise HTTPException(
                status_code=400,
                detail=f"Forecast horizon must be between 1 and {settings.max_forecast_horizon} months"
            )
        
        # Read uploaded file
        contents = await file.read()
        
        # Parse CSV
        try:
            df = pd.read_csv(io.BytesIO(contents))
        except Exception as csv_error:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to read CSV file: {str(csv_error)}"
            )

        # Check if empty
        if df.empty:
            raise HTTPException(
                status_code=400,
                detail="The uploaded CSV file is empty"
            )

        # Prepare and aggregate data
        try:
            monthly_df = prepare_category_data(
                df=df,
                category=category,
                date_col=date_col,
                category_col=category_col,
                units_col=units_col
            )
        except ValueError as ve:
            raise HTTPException(
                status_code=400,
                detail=str(ve)
            )
        
        data_months = len(monthly_df)
        
        # Validate horizon
        validation = validate_forecast_horizon(data_months, horizon)
        if not validation["valid"]:
            raise HTTPException(
                status_code=400,
                detail=validation["message"]
            )
        
        data_summary = get_data_summary(monthly_df)

        # Run forecast
        try:
            forecast_result = run_demand_forecast(
                monthly_df=monthly_df,
                periods=horizon
            )
        except ValueError as ve:
            raise HTTPException(
                status_code=400,
                detail=str(ve)
            )

        # Prepare context
        next_month = monthly_df["ds"].max() + pd.DateOffset(months=1)
        month_name = next_month.strftime("%B %Y")
        
        # Get festivals
        festivals_in_window = get_festivals_for_month(
            next_month.strftime("%B"),
            country
        )

        
        # Parse external factors
        external_factors_dict = {
            "upcoming_promotion": str_to_bool(upcoming_promotion),
            "marketing_campaign": str_to_bool(marketing_campaign),
            "new_product_launch": str_to_bool(new_product_launch),
            "availability_issues": str_to_bool(availability_issues),
            "price_change": price_change,
            "supply_chain_disruption": str_to_bool(supply_chain_disruption),
            "regulatory_changes": str_to_bool(regulatory_changes),
            "logistics_constraints": str_to_bool(logistics_constraints),
            "economic_uncertainty": economic_uncertainty,
            "region": region
        }
                
        # Build external factors summary
        external_factors_summary = []
        if external_factors_dict["upcoming_promotion"]:
            external_factors_summary.append("Upcoming promotion planned")
        if external_factors_dict["marketing_campaign"]:
            external_factors_summary.append("Active marketing campaign")
        if external_factors_dict["new_product_launch"]:
            external_factors_summary.append("New product launch expected")
        if external_factors_dict["availability_issues"]:
            external_factors_summary.append("Availability constraints present")
        if external_factors_dict["price_change"] != "Same":
            external_factors_summary.append(f"Price change: {external_factors_dict['price_change']}")
        if external_factors_dict["supply_chain_disruption"]:
            external_factors_summary.append("Supply chain risk identified")
        if external_factors_dict["regulatory_changes"]:
            external_factors_summary.append("Regulatory changes expected")
        if external_factors_dict["logistics_constraints"]:
            external_factors_summary.append("Logistics constraints present")
        if external_factors_dict["economic_uncertainty"] != "None":
            external_factors_summary.append(f"Economic uncertainty: {external_factors_dict['economic_uncertainty']}")

        # Enhance warnings
        enhanced_warnings = forecast_result.get("warnings", []).copy()
        
        if external_factors_dict["availability_issues"]:
            enhanced_warnings.append("Availability constraints may limit ability to meet forecasted demand")
        if external_factors_dict["supply_chain_disruption"]:
            enhanced_warnings.append("Supply chain disruptions may impact fulfillment capacity")
        if external_factors_dict["price_change"] == "Increase":
            enhanced_warnings.append("Price increase may reduce actual demand below forecast")
        elif external_factors_dict["price_change"] == "Decrease":
            enhanced_warnings.append("Price decrease may drive demand above forecast")
        if external_factors_dict["economic_uncertainty"] in ["Medium", "High"]:
            enhanced_warnings.append(f"{external_factors_dict['economic_uncertainty']} economic uncertainty increases forecast risk")
        
        # Generate AI insight
        ai_insight = generate_ai_insight(
            category=category,
            forecasted_units=forecast_result["forecasted_units"],
            mom_change=forecast_result["mom_change_percent"],
            trend=forecast_result["trend"],
            month=month_name,
            lower_bound=forecast_result.get("lower_bound"),
            upper_bound=forecast_result.get("upper_bound"),
            historical_avg=forecast_result.get("historical_avg"),
            yoy_change=forecast_result.get("yoy_change_percent"),
            data_months=forecast_result.get("data_months"),
            confidence=forecast_result.get("confidence"),
            region=region,
            festivals=festivals_in_window,
            seasonality=forecast_result.get("seasonality"),
            warnings=enhanced_warnings,
            coefficient_of_variation=forecast_result.get("coefficient_of_variation"),
            external_factors=external_factors_dict,
            country=country
        )

        # Return response
        return {
            **forecast_result,
            "ai_insight": ai_insight,
            "data_summary": data_summary,
            "forecast_month": month_name,
            "festivals": festivals_in_window,
            "external_factors": external_factors_summary,
            "region": region,
            "country": country,
            "data_quality_message": forecast_result.get("data_quality_message"),
            "warnings": enhanced_warnings,
            "recommendations": forecast_result.get("recommendations", [])
        }

    except HTTPException:
        raise
    except Exception as e:
        # Log full error
        print(f"Forecast Error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Server error during forecast: {str(e)}"
        )


@app.post("/forecast/evaluate")
async def evaluate_model(
    file: UploadFile,
    category: str = Form(...),
    date_col: str = Form(...),
    category_col: str = Form(...),
    units_col: str = Form(...),
    holdout_months: int = Form(3)
):
    """Evaluate forecast model accuracy."""
    
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))

        monthly_df = prepare_category_data(
            df=df,
            category=category,
            date_col=date_col,
            category_col=category_col,
            units_col=units_col
        )
        
        if len(monthly_df) < holdout_months + settings.min_months_for_analysis:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data for evaluation. Need at least {holdout_months + settings.min_months_for_analysis} months"
            )
        
        evaluation_result = evaluate_forecast_accuracy(
            monthly_df=monthly_df,
            holdout_months=holdout_months
        )
        
        diagnostics = get_model_diagnostics(monthly_df)
        
        return {
            "category": category,
            "evaluation": evaluation_result,
            "diagnostics": diagnostics
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Evaluation Error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500, 
            detail=f"Server error: {str(e)}"
        )


@app.post("/data/summary")
async def get_data_info(
    file: UploadFile,
    category: str = Form(...),
    date_col: str = Form(...),
    category_col: str = Form(...),
    units_col: str = Form(...)
):
    """Get data summary."""
    
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))

        monthly_df = prepare_category_data(
            df=df,
            category=category,
            date_col=date_col,
            category_col=category_col,
            units_col=units_col
        )
        
        summary = get_data_summary(monthly_df)
        diagnostics = get_model_diagnostics(monthly_df)
        
        data_months = len(monthly_df)
        
        if data_months >= settings.optimal_months:
            readiness = "optimal"
            message = "Excellent data quality - ready for highly accurate forecasting"
        elif data_months >= settings.min_months_for_seasonality:
            readiness = "good"
            message = "Good data quality - ready for seasonal forecasting"
        elif data_months >= settings.min_months_for_analysis:
            readiness = "limited"
            message = "Limited data - forecast will be trend-based only"
        else:
            readiness = "insufficient"
            message = f"Insufficient data - need at least {settings.min_months_for_analysis} months"
        
        return {
            "category": category,
            "summary": summary,
            "diagnostics": diagnostics,
            "readiness": readiness,
            "readiness_message": message,
            "ready_for_forecast": data_months >= settings.min_months_for_analysis,
            "can_detect_seasonality": data_months >= settings.min_months_for_seasonality
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Summary Error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500, 
            detail=f"Server error: {str(e)}"
        )
#  LOGISTICS ---



@app.post("/procurement/compare/")
def recommend_supplier(request: ProcurementRequest):
    return {"ai_recommendation": compare_suppliers_with_groq(request.material_name, request.max_days_allowed)}

@app.post("/logistics/plan_route")
def plan_route(request: RouteRequest):
    start_lat, start_lon = get_coordinates(request.start_address)
    end_lat, end_lon = get_coordinates(request.end_address)
    
    if not (start_lat and start_lon):
        raise HTTPException(400, "Invalid Start Address")
    if not (end_lat and end_lon):
        raise HTTPException(400, "Invalid End Address")
        
    waypoint_coords = []
    waypoint_names = []
    if request.waypoints:
        for wp in request.waypoints:
            if wp.strip():
                lat, lon = get_coordinates(wp)
                if lat and lon:
                    waypoint_coords.append((lat, lon))
                    waypoint_names.append(wp)
    
    route_data = get_route_data((start_lat, start_lon), (end_lat, end_lon), waypoint_coords)
    if not route_data:
        raise HTTPException(500, "Could not calc route")
        
    # Enhanced Risk Analysis context
    route_desc = f"from {request.start_address} to {request.end_address}"
    if waypoint_names:
        route_desc += f" via {', '.join(waypoint_names)}"
    
    # Inject metrics into the prompt to prevent hallucination
    metrics_str = f"Calculated Distance: {route_data['distance_km']} km. Est. Duration: {route_data['duration_min']} mins."
    
    prompt = f"""
    Route Consideration: {route_desc}.
    {metrics_str}
    
    Task: Analyze logistics risks for this specific route.
    1. Confirm the distance and duration in your response.
    2. Identify key risks (traffic, road conditions, weather, safety).
    3. Keep it concise.
    """
    
    start_time = datetime.now()
    risk_analysis = analyze_order_with_groq(prompt)
    
    return {
        "start_coords": [start_lat, start_lon],
        "end_coords": [end_lat, end_lon],
        "waypoints": waypoint_coords,
        "route_info": route_data,
        "risk_analysis": risk_analysis
    }

# --- EXTENDED LOGISTICS MANAGEMENT ---

# 1. CARRIERS
@app.post("/logistics/carriers/create")
def create_carrier(carrier: CarrierCreate, db: Session = Depends(database.get_db)):
    db_carrier = models.Carrier(**carrier.dict())
    try:
        db.add(db_carrier)
        db.commit()
        db.refresh(db_carrier)
        return db_carrier
    except Exception as e:
        db.rollback()
        raise HTTPException(400, f"Error creating carrier: {str(e)}")

@app.get("/logistics/carriers/list")
def list_carriers(db: Session = Depends(database.get_db)):
    return db.query(models.Carrier).all()

# 2. DRIVERS
@app.post("/logistics/drivers/create")
def create_driver(driver: DriverCreate, db: Session = Depends(database.get_db)):
    db_driver = models.Driver(**driver.dict())
    try:
        db.add(db_driver)
        db.commit()
        db.refresh(db_driver)
        return db_driver
    except Exception as e:
        db.rollback()
        raise HTTPException(400, f"Error creating driver: {str(e)}")

@app.get("/logistics/drivers/list")
def list_drivers(carrier_id: Optional[int] = None, db: Session = Depends(database.get_db)):
    q = db.query(models.Driver)
    if carrier_id:
        q = q.filter(models.Driver.carrier_id == carrier_id)
    return q.all()

# 3. SHIPMENTS
@app.post("/logistics/shipments/create")
def create_shipment(shipment: ShipmentCreate, db: Session = Depends(database.get_db)):
    # 1. Calculate Route Geometry & Distance first
    start_lat, start_lon = get_coordinates(shipment.origin)
    end_lat, end_lon = get_coordinates(shipment.destination)
    
    if not (start_lat and start_lon and end_lat and end_lon):
        raise HTTPException(400, "Invalid addresses")

    waypoint_coords = []
    if shipment.waypoints:
        for wp in shipment.waypoints:
             lat, lon = get_coordinates(wp)
             if lat: waypoint_coords.append((lat, lon))

    route_data = get_route_data((start_lat, start_lon), (end_lat, end_lon), waypoint_coords)
    
    # 2. Prepare DB Object
    db_shipment = models.Shipment(
        tracking_number=shipment.tracking_number,
        origin=shipment.origin,
        destination=shipment.destination,
        waypoints=json.dumps(shipment.waypoints),
        carrier_id=shipment.carrier_id,
        driver_id=shipment.driver_id,
        status="SCHEDULED",
        origin_lat=start_lat,  # Store origin coordinates
        origin_lon=start_lon,
        origin_snapped=False,
        current_location_lat=start_lat,
        current_location_lon=start_lon,
        progress_percent=0.0
    )
    
    if route_data:
        db_shipment.route_geometry = route_data['geometry']
        db_shipment.total_distance_km = route_data['distance_km']
        # Estimate ETA (Distance / 60km/h + buffer)
        hours = route_data['duration_min'] / 60
        db_shipment.eta = datetime.now() + timedelta(hours=hours)

    if shipment.scheduled_date:
        # Simple ISO parsing
        try:
            db_shipment.scheduled_date = datetime.fromisoformat(shipment.scheduled_date)
        except: pass

    try:
        db.add(db_shipment)
        db.commit()
        db.refresh(db_shipment)
        return db_shipment
    except Exception as e:
        db.rollback()
        raise HTTPException(400, f"Error creating shipment: {str(e)}")

@app.get("/logistics/shipments/list")
def list_shipments(db: Session = Depends(database.get_db)):
    return db.query(models.Shipment).all()

@app.post("/logistics/shipments/{id}/update")
def update_shipment(id: int, update: ShipmentUpdate, db: Session = Depends(database.get_db)):
    shipment = db.query(models.Shipment).filter(models.Shipment.id == id).first()
    if not shipment:
        raise HTTPException(404, "Shipment not found")
    
    # AUTO-CALCULATE PROGRESS if coordinates are updated
    if update.current_location_lat and update.current_location_lon:
        try:
            from geopy.distance import geodesic
            
            # SNAP-TO-START LOGIC (Robust Version)
            # If this is the FIRST coordinate update from the driver, snap the origin
            if not shipment.origin_snapped:
                # Update origin to the actual reported GPS location
                shipment.origin_lat = update.current_location_lat
                shipment.origin_lon = update.current_location_lon
                shipment.origin_snapped = True
                
                # Recalculate and FIX Total Distance based on real starting point
                # This ensures the denominator is correct for percentage
                dest_lat, dest_lon = get_coordinates(shipment.destination)
                if dest_lat:
                    origin_point = (shipment.origin_lat, shipment.origin_lon)
                    dest_point = (dest_lat, dest_lon)
                    shipment.total_distance_km = geodesic(origin_point, dest_point).kilometers
                
                shipment.progress_percent = 0.0
                print(f"✅ Snapped origin for {shipment.tracking_number} to {shipment.origin_lat}, {shipment.origin_lon}")
            
            else:
                # Normal update: Calculate progress from snapped origin
                origin_point = (shipment.origin_lat, shipment.origin_lon)
                current_point = (update.current_location_lat, update.current_location_lon)
                
                # Get destination (hopefully cached or geocoded)
                dest_lat, dest_lon = get_coordinates(shipment.destination)
                if dest_lat and shipment.total_distance_km > 0:
                    distance_traveled = geodesic(origin_point, current_point).kilometers
                    progress = min(100.0, (distance_traveled / shipment.total_distance_km) * 100)
                    shipment.progress_percent = round(progress, 2)
                        
        except Exception as e:
            print(f"Progress calculation error: {e}")
    
    # Update Status (moved down to allow SNAP logic to check previous status)
    if update.status: shipment.status = update.status
    if update.current_location_lat: shipment.current_location_lat = update.current_location_lat
    if update.current_location_lon: shipment.current_location_lon = update.current_location_lon
    if update.progress_percent is not None: shipment.progress_percent = update.progress_percent
    
    db.commit()
    return shipment

