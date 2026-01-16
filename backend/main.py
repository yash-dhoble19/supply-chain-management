# backend/main.py - FIXED VERSION WITH PROPER CORS
# ---------------

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
        "message": "Backend is running successfully!",
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
