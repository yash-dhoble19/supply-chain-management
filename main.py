from fastapi import FastAPI, Depends, HTTPException, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from openai import OpenAI
import models, database
import pandas as pd
import io
import json
import os
import traceback
from dotenv import load_dotenv
from geopy.geocoders import Nominatim
import requests

from data_preparation import prepare_category_data, get_data_summary
from forecast_service import run_demand_forecast
from ai_insight_service import generate_ai_insight
from evaluation import evaluate_forecast_accuracy, get_model_diagnostics
from config import settings, get_festivals_for_month, validate_forecast_horizon

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

# --- 3. HELPER FUNCTIONS ---

def analyze_order_with_groq(address):
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "Risk Manager. Mark HIGH/LOW RISK."}, {"role": "user", "content": address}]
        )
        return response.choices[0].message.content
    except: return "AI Error"

def compare_suppliers_with_groq(material, max_days):
    try:
        prompt = f"Buy {material} in {max_days} days. Pick best supplier."
        response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
        return response.choices[0].message.content
    except: return "AI Error"

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

def get_route_data(start_coords, end_coords):
    start_str = f"{start_coords[1]},{start_coords[0]}"
    end_str = f"{end_coords[1]},{end_coords[0]}"
    url = f"http://router.project-osrm.org/route/v1/driving/{start_str};{end_str}?overview=full"
    
    try:
        response = requests.get(url)
        data = response.json()
        if data["code"] == "Ok":
            route = data["routes"][0]
            return {
                "distance_km": round(route["distance"] / 1000, 2),
                "duration_min": round(route["duration"] / 60, 0),
                "geometry": route["geometry"]
            }
        return None
    except:
        return None

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
    
    # Sort by score descending
    supplier_scores.sort(key=lambda x: x["score"], reverse=True)
    return supplier_scores[0]["supplier"] if supplier_scores else None

def generate_ai_morning_briefing(health_score, critical_count, pending_pos, db: Session):
    """
    Uses LLM to generate a strategic morning briefing
    """
    products = db.query(models.Product).all()
    critical_products = [p.name for p in products if p.current_stock < (p.optimal_stock_level * 0.2)][:3]
    
    prompt = f"""
    You are a Supply Chain Director AI. Generate a comprehensive morning briefing (detailed analysic and one paragraph ).
    
    Data:
    - Health Score: {health_score}/100
    - Critical Items: {critical_count} (Examples: {', '.join(critical_products) if critical_products else 'None'})
    - Pending POs: {pending_pos}
    
    Requirements:
    - Provide a detailed analysis (need  one paragraph explaintion)
    - Include executive summary
    - Discuss health score implications
    - Analyze critical items and their impact
    - Review pending POs and their urgency
    - Provide actionable recommendations
    - Include strategic insights for the day
    
    Tone: Professional, actionable, and strategic. Highlight the most urgent concern first, then provide comprehensive analysis.
    """
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except:
        return "Market conditions are stable. Review critical items and expedite pending orders. Health score indicates attention needed in supply chain operations. Prioritize addressing critical inventory levels and monitor pending purchase orders closely."

def generate_urgency_reasoning(product, supplier):
    """
    Uses LLM to explain WHY a product needs urgent attention
    """
    stock_pct = (product.current_stock / product.optimal_stock_level * 100) if product.optimal_stock_level > 0 else 0
    
    prompt = f"""
    Generate a 1-2 sentence urgent reasoning for procurement.
    
    Product: {product.name}
    Current Stock: {product.current_stock} ({stock_pct:.0f}% of optimal)
    Best Supplier: {supplier.name} ({supplier.delivery_speed_days} days delivery)
    
    Be direct and actionable.
    """
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except:
        return f"Stock critically low at {stock_pct:.0f}%. Immediate replenishment required."

# --- 4. API ENDPOINTS ---

# --- NEW: PROCUREMENT ENDPOINTS ---

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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Email Generation Failed: {str(e)}")

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
        # Check if API key is configured
        if not GROQ_API_KEY:
            raise HTTPException(
                status_code=500, 
                detail="GROQ_API_KEY not configured. Check your .env file."
            )
        
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
        raise HTTPException(
            status_code=500, 
            detail=f"AI returned invalid JSON: {str(e)}"
        )
    except Exception as e:
        # Log the full error for debugging
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"AI Parse Failed: {str(e)}"
        )

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
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/ai/generate_reorder_email")
def generate_reorder_email(req: ReorderRequest):
    return draft_negotiation_email(req)

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
    if not start_lat:
        raise HTTPException(400, "Invalid Address")
    
    route_data = get_route_data((start_lat, start_lon), (end_lat, end_lon))
    return {
        "start_coords": [start_lat, start_lon],
        "end_coords": [end_lat, end_lon],
        "route_info": route_data,
        "risk_analysis": analyze_order_with_groq(request.end_address)
    }