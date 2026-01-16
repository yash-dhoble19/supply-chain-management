

# demand_forecast/api.py
# Extracted from your friend's backend/main.py
# This runs as a separate microservice on Port 8001

from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import io
import pandas as pd
from typing import Optional
import traceback

from .data_preparation import prepare_category_data, get_data_summary
from .forecast_service import run_demand_forecast
from .ai_insight_service import generate_ai_insight
from .evaluation import evaluate_forecast_accuracy, get_model_diagnostics
from .config import settings, get_festivals_for_month, validate_forecast_horizon

# Initialize FastAPI app
app = FastAPI(
    title="Demand Forecasting Service",
    version="1.0.0",
    description="AI-powered demand forecasting microservice"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        "service": "Demand Forecasting API",
        "version": "1.0.0"
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
    """Validate uploaded data and return horizon availability."""
    try:
        contents = await file.read()
        
        try:
            df = pd.read_csv(io.BytesIO(contents))
        except Exception as csv_error:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to read CSV: {str(csv_error)}"
            )
        
        if df.empty:
            raise HTTPException(status_code=400, detail="Empty CSV file")
        
        # Validate columns
        missing_cols = []
        for col, name in [(date_col, "Date"), (category_col, "Category"), (units_col, "Units")]:
            if col not in df.columns:
                missing_cols.append(f"{name} column '{col}'")
        
        if missing_cols:
            raise HTTPException(
                status_code=400,
                detail=f"Missing columns: {', '.join(missing_cols)}"
            )
        
        # Prepare data
        monthly_df = prepare_category_data(
            df=df,
            category=category,
            date_col=date_col,
            category_col=category_col,
            units_col=units_col
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
            "ready_for_forecast": ready_for_forecast
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/forecast/upload")
async def upload_and_forecast(
    file: UploadFile,
    category: str = Form(...),
    date_col: str = Form(...),
    category_col: str = Form(...),
    units_col: str = Form(...),
    horizon: int = Form(1),
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
    """Generate AI-powered demand forecast."""
    try:
        if horizon < 1 or horizon > settings.max_forecast_horizon:
            raise HTTPException(
                status_code=400,
                detail=f"Horizon must be 1-{settings.max_forecast_horizon}"
            )
        
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        if df.empty:
            raise HTTPException(status_code=400, detail="Empty CSV")
        
        # Prepare data
        monthly_df = prepare_category_data(
            df=df,
            category=category,
            date_col=date_col,
            category_col=category_col,
            units_col=units_col
        )
        
        data_months = len(monthly_df)
        validation = validate_forecast_horizon(data_months, horizon)
        
        if not validation["valid"]:
            raise HTTPException(status_code=400, detail=validation["message"])
        
        data_summary = get_data_summary(monthly_df)
        
        # Run forecast
        forecast_result = run_demand_forecast(
            monthly_df=monthly_df,
            periods=horizon
        )
        
        # Prepare context
        next_month = monthly_df["ds"].max() + pd.DateOffset(months=1)
        month_name = next_month.strftime("%B %Y")
        
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
        # ... add other factors as in original
        
        # Enhanced warnings
        enhanced_warnings = forecast_result.get("warnings", []).copy()
        
        if external_factors_dict["availability_issues"]:
            enhanced_warnings.append("Availability constraints may limit fulfillment")
        
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
        
        return {
            **forecast_result,
            "ai_insight": ai_insight,
            "data_summary": data_summary,
            "forecast_month": month_name,
            "festivals": festivals_in_window,
            "external_factors": external_factors_summary,
            "region": region,
            "country": country,
            "warnings": enhanced_warnings
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# Add other endpoints from friend's code (evaluate, data summary, etc.)