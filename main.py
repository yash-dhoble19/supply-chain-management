from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel
from openai import OpenAI
import models, database
import pandas as pd
import io
import json

# --- LOGISTICS IMPORTS (FREE OPEN SOURCE) ---
from geopy.geocoders import Nominatim
import requests
import polyline

# --- CONFIGURATION ---
GROQ_API_KEY = "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"

# Initialize AI
client = OpenAI(
    api_key=GROQ_API_KEY, 
    base_url="https://api.groq.com/openai/v1"
)

# Initialize Database
models.Base.metadata.create_all(bind=database.engine)

# Initialize Free Geocoder (OpenStreetMap)
# User-agent is required by Nominatim terms of service
geolocator = Nominatim(user_agent="scm_app_free_v1")

app = FastAPI(title="GenAI Supply Chain API")

# --- Pydantic Schemas ---
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

class RouteRequest(BaseModel):
    start_address: str
    end_address: str

# --- AI Helper Functions ---
def analyze_order_with_groq(address):
    """ Agent 1: Logistics Risk Analyzer """
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a Risk Manager. If address is remote/warzone, mark HIGH RISK. Start with '⚠️ HIGH RISK' or '✅ LOW RISK'."},
                {"role": "user", "content": f"Address: {address}"}
            ],
            stream=False
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ AI Analysis Failed: {str(e)}"

def compare_suppliers_with_groq(material, max_days):
    """ Agent 2: Procurement Negotiator """
    supplier_data = """
    1. TechVendor Global: $12.50/unit, Delivers in 5 days, Reliability: 9/10
    2. Fashion Wholesale: $8.00/unit, Delivers in 12 days, Reliability: 8/10
    3. Organic Foods Dist: $15.00/unit, Delivers in 4 days, Reliability: 10/10
    """
    prompt = f"""
    Buy '{material}'. Deadline: {max_days} days.
    Quotes: {supplier_data}
    Pick best supplier. Reject if > {max_days} days.
    Output format: SELECTED: [Name] REASON: [Text] DRAFT EMAIL: [Text]
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

def analyze_market_factors_with_groq(category, current_trend_percentage):
    """ Agent 3: Demand Forecasting Strategist """
    prompt = f"""
    Product Category: {category}
    Math Trend: {current_trend_percentage:.1f}% growth.
    Current Date: Dec 2024.
    
    Task:
    1. Analyze seasonality and market news.
    2. Suggest a 'Final Forecast Adjustment' factor (e.g. 1.15).
    3. Provide insight text.
    4. List 3 external factors with impact score (0-100) and sentiment (Positive/Negative).

    Output JSON ONLY:
    {{
        "ai_adjustment_factor": 1.15, 
        "insight_text": "...",
        "external_factors": [
            {{"name": "Holiday Season", "impact": "Positive", "score": 90}}
        ]
    }}
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Output ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"} 
        )
        return response.choices[0].message.content
    except Exception as e:
        return '{"error": "AI failed"}'

# --- LOGISTICS ENGINE (FREE / OSRM VERSION) ---
def get_coordinates(address):
    """
    Uses Nominatim (OpenStreetMap) to convert Address -> Lat/Lon
    Free to use, no API Key required.
    """
    try:
        location = geolocator.geocode(address)
        if location:
            return location.latitude, location.longitude
        return None, None
    except Exception as e:
        print(f"Geocoding Error: {e}")
        return None, None

def get_route_data(start_coords, end_coords):
    """
    Uses OSRM Public API to calculate route.
    Free to use, no API Key required.
    """
    # OSRM requires coordinates in (Longitude, Latitude) order
    start_str = f"{start_coords[1]},{start_coords[0]}"
    end_str = f"{end_coords[1]},{end_coords[0]}"
    
    url = f"http://router.project-osrm.org/route/v1/driving/{start_str};{end_str}?overview=full"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if data["code"] == "Ok":
            route = data["routes"][0]
            # OSRM returns geometry as a polyline string compatible with Google/Folium
            geometry = route["geometry"]
            
            return {
                "distance_km": round(route["distance"] / 1000, 2),
                "duration_min": round(route["duration"] / 60, 0),
                "geometry": geometry
            }
        return None
    except Exception as e:
        print(f"Routing Error: {e}")
        return None

# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"message": "Supply Chain AI System is Online 🚀"}

# 1. ORDER MANAGEMENT
@app.post("/orders/", response_model=OrderResponse)
def create_order(order: OrderCreate, db: Session = Depends(database.get_db)):
    risk = analyze_order_with_groq(order.delivery_address)
    db_order = models.Order(customer_name=order.customer_name, delivery_address=order.delivery_address, status="PENDING", ai_risk_assessment=risk)
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

@app.get("/orders/", response_model=List[OrderResponse])
def read_orders(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    return db.query(models.Order).offset(skip).limit(limit).all()

# 2. INVENTORY MANAGEMENT
@app.get("/inventory/analysis")
def analyze_inventory(db: Session = Depends(database.get_db)):
    results = []
    products = db.query(models.Product).all()
    for product in products:
        incoming_stock = 0 
        total = product.current_stock + incoming_stock
        status = "OK"
        rec = "Optimal"
        if total < product.safety_stock_level:
            status = "CRITICAL"
            rec = "⚠️ Stockout Risk! Replenish immediately."
        results.append({
            "product": product.name, "sku": product.sku, "on_hand": product.current_stock,
            "incoming_po": incoming_stock, "safety_stock": product.safety_stock_level,
            "status": status, "ai_recommendation": rec
        })
    return results

# 3. PROCUREMENT
@app.post("/procurement/compare/")
def recommend_supplier(request: ProcurementRequest):
    return {"ai_recommendation": compare_suppliers_with_groq(request.material_name, request.max_days_allowed)}

# 4. ROBUST DEMAND FORECASTING
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

# 5. LOGISTICS ROUTE PLANNING (FREE OPEN SOURCE)
@app.post("/logistics/plan_route")
def plan_route(request: RouteRequest):
    # 1. Geocode (Free Nominatim)
    start_lat, start_lon = get_coordinates(request.start_address)
    end_lat, end_lon = get_coordinates(request.end_address)
    
    if not start_lat or not end_lat:
        raise HTTPException(status_code=400, detail="Address not found. Try a major city.")
        
    # 2. Get Route (Free OSRM)
    route_data = get_route_data((start_lat, start_lon), (end_lat, end_lon))
    if not route_data:
        raise HTTPException(status_code=500, detail="Routing failed.")

    # 3. Analyze Risk (AI)
    risk_analysis = analyze_order_with_groq(request.end_address)

    return {
        "start_coords": [start_lat, start_lon],
        "end_coords": [end_lat, end_lon],
        "route_info": route_data,
        "risk_analysis": risk_analysis
    }