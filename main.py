from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from openai import OpenAI
import models, database
import pandas as pd
import io
import json
import os
from dotenv import load_dotenv
from geopy.geocoders import Nominatim
import requests

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

app = FastAPI(title="GenAI Supply Chain API")

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

# AI Feature Schemas
class AIProductParseRequest(BaseModel):
    description: str

class PricingRequest(BaseModel):
    product_name: str
    current_price: float
    current_stock: int
    optimal_stock: int
    category: str

# Inventory Report Schema
class InventoryReportRequest(BaseModel):
    products: List[dict]

# Order & Logistics Schemas
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

# --- 4. API ENDPOINTS ---

@app.get("/")
def read_root():
    return {"message": "Supply Chain AI System is Online 🚀"}

# --- AI AGENTS (Smart Pricing, Onboarding, Audit, Sim) ---

@app.post("/ai/pricing_analysis")
def analyze_pricing_strategy(req: PricingRequest):
    """
    AI Agent with STRICT math logic to prevent hallucinations.
    """
    # 1. Python calculates the ratio first (The Brain)
    ratio = req.current_stock / req.optimal_stock if req.optimal_stock > 0 else 0
    
    # 2. We inject the exact math into the prompt
    prompt = f"""
    You are a Strategic Pricing Pricing Algorithm.
    
    DATA:
    - Product: {req.product_name}
    - Current Price: ${req.current_price}
    - Stock Ratio (Current/Optimal): {ratio:.2f} (This is {ratio*100:.0f}%)
    
    LOGIC RULES (FOLLOW STRICTLY):
    1. IF Stock Ratio > 1.5 (Over 150%): You MUST suggest LOWER price (Discount) to clear space.
    2. IF Stock Ratio < 0.3 (Under 30%): You MUST suggest HIGHER price (Premium) due to scarcity.
    3. IF Stock Ratio is between 0.3 and 1.5: You MUST suggest HOLD (Keep same price) because inventory is healthy.
    
    OUTPUT JSON ONLY:
    {{
        "new_price": (Float - calculate based on rule),
        "action": "RAISE" or "LOWER" or "HOLD",
        "reason": "Explain using the Stock Ratio logic.",
        "confidence": 95
    }}
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a logic engine. Output strict JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Pricing Failed: {str(e)}")

@app.post("/ai/parse_product_info")
def parse_product_info(request: AIProductParseRequest):
    """
    Takes raw string and returns structured JSON for frontend form.
    """
    prompt = f"""
    You are a Supply Chain Data Entry Assistant.
    User Input: "{request.description}"
    
    Task: Extract product details. If information is missing, INTELLIGENTLY GUESS based on industry standards.
    
    Output JSON ONLY:
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
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You output strictly valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Parse Failed: {str(e)}")

@app.post("/ai/audit_inventory")
def audit_inventory(req: InventoryReportRequest):
    data_summary = "\n".join([f"- {p['product']} ({p['category']}): Stock {p['on_hand']}/{p['optimal_stock']}, Price ${p['unit_price']}" for p in req.products])
    prompt = f"""
    You are a Supply Chain CFO. Current Inventory: {data_summary}
    Task: Write a Strategic Audit Report (Markdown).
    Include: Executive Summary, Critical Risks, Financial efficiency, Top 3 Recommendations.
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
    context = "\n".join([f"- {p['product']}: Stock {p['on_hand']}, Price ${p['unit_price']}" for p in req.products])
    prompt = f"""
    Risk Analyst. Inventory: {context}. SCENARIO: "{req.scenario}"
    Analyze impact. Output JSON: impact_score (0-100), impact_summary, affected_products (list), recommendation.
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "JSON only."}, {"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e: raise HTTPException(500, str(e))

@app.post("/ai/generate_reorder_email")
def generate_reorder_email(req: ReorderRequest):
    needed = max(0, req.optimal_stock - req.current_stock)
    if needed == 0: needed = 100
    cost = needed * req.unit_price
    prompt = f"""
    Write PO email. Supplier: {req.supplier_name}. Product: {req.product_name}. Qty: {needed}. Cost: ${cost}.
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        return {"email_draft": response.choices[0].message.content, "recommended_qty": needed}
    except Exception as e: raise HTTPException(500, str(e))

# --- INVENTORY CRUD ---

@app.post("/products/")
def create_product(product: ProductCreate, db: Session = Depends(database.get_db)):
    existing = db.query(models.Product).filter(models.Product.sku == product.sku).first()
    if existing: raise HTTPException(status_code=400, detail="SKU exists")
    db_product = models.Product(**product.dict())
    db.add(db_product)
    db.commit()
    return {"message": "Created", "id": db_product.id}

@app.put("/products/{product_id}")
def update_product(product_id: int, product: ProductUpdate, db: Session = Depends(database.get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product: raise HTTPException(status_code=404, detail="Product not found")
    
    if product.stage: db_product.stage = product.stage
    if product.current_stock is not None: db_product.current_stock = product.current_stock
    if product.unit_price is not None: db_product.unit_price = product.unit_price
    if product.category: db_product.category = product.category
    
    db.commit()
    return {"message": "Updated"}

@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(database.get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product: raise HTTPException(status_code=404, detail="Product not found")
    db.delete(db_product)
    db.commit()
    return {"message": "Product deleted"}

@app.post("/inventory/logs")
def log_stock_movement(movement: StockMovement, db: Session = Depends(database.get_db)):
    product = db.query(models.Product).filter(models.Product.id == movement.product_id).first()
    if not product: raise HTTPException(status_code=404, detail="Product not found")

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
            "product": p.name, "sku": p.sku, 
            "on_hand": p.current_stock, "safety_stock": p.safety_stock_level, 
            "optimal_stock": p.optimal_stock_level, "unit_price": p.unit_price, 
            "category": p.category, "stage": p.stage, 
            "status": status, "ai_recommendation": rec
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

# --- FORECASTING, PROCUREMENT, LOGISTICS ---

@app.post("/forecast/upload")
async def generate_forecast(category: str = Form(...), file: UploadFile = File(...)):
    contents = await file.read()
    df = pd.read_csv(io.BytesIO(contents))
    df = df.loc[:, ~df.columns.duplicated()]

    if 'Date' not in df.columns: return {"error": "Missing 'Date' column."}
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date']) 

    if 'Category' in df.columns: df_filtered = df[df['Category'] == category].copy()
    else: df_filtered = df.copy()

    if df_filtered.empty: return {"error": f"No data found for category: '{category}'"}

    if 'Total_Revenue' not in df_filtered.columns:
        if 'Quantity' in df_filtered.columns and 'Unit_Price' in df_filtered.columns:
            df_filtered['Total_Revenue'] = df_filtered['Quantity'] * df_filtered['Unit_Price']
        else: return {"error": "Missing 'Total_Revenue' column."}

    df_monthly = df_filtered.set_index('Date').resample('ME')['Total_Revenue'].sum().reset_index()
    if len(df_monthly) < 2: return {"error": "Not enough data."}
         
    start_val = float(df_monthly['Total_Revenue'].iloc[0])
    end_val = float(df_monthly['Total_Revenue'].iloc[-1])
    trend_pct = 0 if start_val == 0 else ((end_val - start_val) / start_val) * 100

    try:
        ai_response_str = analyze_market_factors_with_groq(category, trend_pct)
        ai_data = json.loads(ai_response_str)
    except: ai_data = {"ai_adjustment_factor": 1.0, "insight_text": "Unavailable", "external_factors": []}
        
    adjustment = ai_data.get("ai_adjustment_factor", 1.0)
    last_date = df_monthly['Date'].iloc[-1]
    last_val = end_val
    forecast_points = []
    
    for i in range(1, 7): 
        next_date = last_date + pd.DateOffset(months=i)
        next_val = last_val * (1 + (trend_pct / 100 / 12)) * adjustment
        forecast_points.append({"Date": next_date.strftime("%Y-%m-%d"), "Sales": int(next_val), "Type": "Forecast"})
        last_val = next_val

    history_points = []
    for _, row in df_monthly.iterrows():
        history_points.append({"Date": row['Date'].strftime("%Y-%m-%d"), "Sales": int(row['Total_Revenue']), "Type": "Historical"})

    return {
        "category": category, "historical_trend": trend_pct,
        "ai_insight": ai_data.get("insight_text"), "external_factors": ai_data.get("external_factors"),
        "chart_data": history_points + forecast_points
    }

@app.post("/procurement/compare/")
def recommend_supplier(request: ProcurementRequest):
    return {"ai_recommendation": compare_suppliers_with_groq(request.material_name, request.max_days_allowed)}

@app.post("/logistics/plan_route")
def plan_route(request: RouteRequest):
    start_lat, start_lon = get_coordinates(request.start_address)
    end_lat, end_lon = get_coordinates(request.end_address)
    if not start_lat: raise HTTPException(400, "Invalid Address")
    
    route_data = get_route_data((start_lat, start_lon), (end_lat, end_lon))
    return {
        "start_coords": [start_lat, start_lon],
        "end_coords": [end_lat, end_lon],
        "route_info": route_data,
        "risk_analysis": analyze_order_with_groq(request.end_address)
    }