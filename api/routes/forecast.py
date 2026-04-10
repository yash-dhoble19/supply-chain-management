"""
Forecasting routes — /forecast/*, /validate-data, /data/summary
These remain mostly unchanged as they use dedicated external modules.
"""
import io
import traceback
import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, Form, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
import database
from config import settings, get_festivals_for_month, validate_forecast_horizon
from data_preparation import prepare_category_data, get_data_summary
from forecast_service import run_demand_forecast
from ai_insight_service import generate_ai_insight
from evaluation import evaluate_forecast_accuracy, get_model_diagnostics
from services.background_tasks import generate_and_store_insight
from prophet_model import DemandProphetModel

router = APIRouter(tags=["Forecasting"])


# ---------------------------------------------------------------------------
# JSON-based Prophet prediction endpoint (called by frontend directly)
# ---------------------------------------------------------------------------

class PredictRequest(BaseModel):
    dates: List[str]
    sales: List[float]
    forecastDays: int = 30
    timeGrouping: str = "Daily"


@router.post("/forecast/predict")
async def predict_from_json(req: PredictRequest):
    """
    Accept cleaned date+sales arrays from the frontend, run the real
    Facebook Prophet model, and return a ForecastSection-compatible
    JSON payload so the UI can render it without any client-side heuristic.
    """
    try:
        if len(req.dates) != len(req.sales):
            raise HTTPException(400, "dates and sales arrays must have the same length")
        if len(req.dates) < 2:
            raise HTTPException(400, "Need at least 2 data points to forecast")

        # --- Build the Prophet dataframe ---
        df = pd.DataFrame({"ds": pd.to_datetime(req.dates, errors="coerce"), "y": req.sales})
        df = df.dropna(subset=["ds"])
        df["y"] = pd.to_numeric(df["y"], errors="coerce").fillna(0).clip(lower=0)
        df = df.sort_values("ds").reset_index(drop=True)

        if df.empty or len(df) < 2:
            raise HTTPException(400, "Insufficient valid data points after cleaning")

        # --- Aggregate by timeGrouping ---
        freq_map = {"Daily": "D", "Weekly": "W", "Monthly": "MS"}
        freq = freq_map.get(req.timeGrouping, "D")
        agg_df = df.set_index("ds")["y"].resample(freq).sum().reset_index()
        agg_df = agg_df.sort_values("ds").reset_index(drop=True)

        data_points = len(agg_df)

        # --- Data sufficiency check (Relaxed for demo/samples) ---
        data_span_days = (agg_df["ds"].max() - agg_df["ds"].min()).days
        if req.timeGrouping == "Daily" and data_span_days < 7:
            raise HTTPException(400, f"Daily forecast requires at least 1 week of data. Only {data_span_days} days found.")
        elif req.timeGrouping == "Weekly" and data_span_days < 28:
            raise HTTPException(400, f"Weekly forecast requires at least 4 weeks of data. Only ~{data_span_days // 7} weeks found.")
        elif req.timeGrouping == "Monthly" and data_span_days < 60:
            raise HTTPException(400, f"Monthly forecast requires at least 2 months of data. Only ~{data_span_days // 30} months found.")

        # --- Run Prophet ---
        model = DemandProphetModel(
            data_months=max(1, data_span_days // 30),
            freq=freq,
            add_country_holidays="IN"
        )
        model.train(agg_df)
        forecast_df = model.forecast(periods=req.forecastDays)

        # --- Build response in ForecastSection shape ---
        # Historical points
        historical = []
        for _, row in agg_df.iterrows():
            historical.append({
                "date": row["ds"].strftime("%Y-%m-%d"),
                "value": round(float(row["y"]), 2)
            })

        # Forecast points
        forecast_points = []
        applied_festival_days = 0
        for _, row in forecast_df.iterrows():
            date_str = row["Date"].strftime("%Y-%m-%d") if hasattr(row["Date"], "strftime") else str(row["Date"])[:10]
            value = max(0, float(row["Forecasted_Units"]))
            lower = max(0, float(row["Lower_Bound"]))
            # Ensure lower bound is at least 1 if forecast is positive
            if value > 0 and lower < 1:
                lower = max(1, round(value * 0.8))
            upper = max(0, float(row["Upper_Bound"]))
            forecast_points.append({
                "date": date_str,
                "forecast": round(value, 2),
                "lowerBound": round(lower, 2),
                "upperBound": round(upper, 2),
            })

        # Metrics
        forecast_values = [fp["forecast"] for fp in forecast_points]
        total_forecast = round(sum(forecast_values), 2)
        avg_daily = round(total_forecast / max(1, len(forecast_values)), 2)
        min_forecast = round(min(forecast_values), 2) if forecast_values else 0
        max_forecast = round(max(forecast_values), 2) if forecast_values else 0

        # Trend detection
        if len(forecast_values) >= 2:
            first_val = forecast_values[0]
            last_val = forecast_values[-1]
            if last_val > first_val * 1.02:
                trend = "increasing"
            elif last_val < first_val * 0.98:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "stable"

        # Confidence based on data length
        if data_points >= 180:
            confidence = "High"
        elif data_points >= 60:
            confidence = "Medium"
        else:
            confidence = "Low"

        # Demand type classification (descriptive only)
        raw_values = agg_df["y"].values
        zero_ratio = float(np.sum(raw_values == 0)) / max(1, len(raw_values))
        cv = float(np.std(raw_values) / max(1, np.mean(raw_values))) if np.mean(raw_values) > 0 else 0

        if len(raw_values) < 10:
            demand_type = "New"
        elif zero_ratio > 0.3:
            demand_type = "Intermittent"
        elif cv > 1.0:
            demand_type = "Erratic"
        elif cv < 0.3:
            demand_type = "Smooth"
        else:
            demand_type = "Seasonal"

        return {
            "status": "success",
            "sectionName": "Overall Demand Forecast",
            "chart": {
                "history": historical,
                "forecast": [{"date": fp["date"], "p10": fp["lowerBound"], "p50": fp["forecast"], "p90": fp["upperBound"]} for fp in forecast_points]
            },
            "metrics": {
                "totalForecast": total_forecast,
                "avgDailyForecast": avg_daily,
                "minForecast": min_forecast,
                "maxForecast": max_forecast,
            },
            "table": [{"date": fp["date"], "forecast": fp["forecast"], "lowerBound": fp["lowerBound"], "upperBound": fp["upperBound"]} for fp in forecast_points],
            "smart": {
                "summary": {
                    "forecastTotal": total_forecast,
                    "avgDailyDemand": avg_daily,
                    "trend": trend,
                    "demandType": demand_type,
                    "confidence": confidence,
                },
                "model": {
                    "name": "Facebook Prophet",
                    "reason": "Backend statistical decomposition — trend + seasonality + holiday effects via Prophet",
                },
                "historical": historical,
                "forecast": forecast_points,
                "meta": {
                    "appliedFestivalDays": applied_festival_days,
                    "dataPointsUsed": data_points,
                }
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"Prophet forecast failed: {e}")


def _str_to_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in ("true", "1", "yes", "on")


@router.post("/validate-data")
async def validate_data(
    file: UploadFile, category: str = Form(...),
    date_col: str = Form(...), category_col: str = Form(...), units_col: str = Form(...),
    time_grouping: str = Form("Monthly"),
):
    try:
        filename = getattr(file, "filename", "").lower()
        if not (filename.endswith(".csv") or filename.endswith(".xlsx") or filename.endswith(".xls")):
            raise HTTPException(400, "Invalid format. Please upload a CSV or Excel file.")

        contents = await file.read()
        try:
            if filename.endswith(".csv"):
                df = pd.read_csv(io.BytesIO(contents))
            else:
                df = pd.read_excel(io.BytesIO(contents))
        except Exception as e:
            raise HTTPException(400, f"Failed to read file: {e}")
            
        if df.empty:
            raise HTTPException(400, "Uploaded file is empty.")

        missing = [name for col, name in [(date_col, "Date"), (category_col, "Category"), (units_col, "Units")] if col not in df.columns]
        if missing:
            raise HTTPException(400, f"Missing columns: {', '.join(missing)}. Available: {', '.join(df.columns.tolist())}")

        try:
            monthly_df = prepare_category_data(df=df, category=category, date_col=date_col, category_col=category_col, units_col=units_col, time_grouping=time_grouping)
        except ValueError as ve:
            raise HTTPException(400, str(ve))

        data_months = len(monthly_df)
        data_summary = get_data_summary(monthly_df)
        horizon_validation = {}
        for h in [1, 3, 6]:
            v = validate_forecast_horizon(data_months, h)
            horizon_validation[f"{h}_month"] = {"allowed": v["valid"], "message": v["message"], "confidence": v["confidence"]}

        return {
            "status": "success", "category": category, "data_summary": data_summary,
            "horizon_validation": horizon_validation,
            "available_horizons": [h for h in [1, 3, 6] if horizon_validation[f"{h}_month"]["allowed"]],
            "ready_for_forecast": data_months >= settings.min_months_for_analysis,
            "readiness_message": (
                "✅ Data is sufficient for forecasting" if data_months >= settings.min_months_for_analysis
                else f"❌ Need {settings.min_months_for_analysis} months minimum, have {data_months}"
            ),
        }
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"Server error during validation: {e}")


@router.post("/forecast/upload")
async def upload_and_forecast(
    file: UploadFile, background_tasks: BackgroundTasks,
    db: Session = Depends(database.get_db), category: str = Form(...),
    date_col: str = Form(...), category_col: str = Form(...), units_col: str = Form(...),
    time_grouping: str = Form("Monthly"),
    horizon: int = Form(1),
    upcoming_promotion: str = Form("false"), marketing_campaign: str = Form("false"),
    new_product_launch: str = Form("false"), availability_issues: str = Form("false"),
    price_change: str = Form("Same"), supply_chain_disruption: str = Form("false"),
    regulatory_changes: str = Form("false"), logistics_constraints: str = Form("false"),
    economic_uncertainty: str = Form("None"), region: str = Form("India"), country: str = Form("IN"),
):
    try:
        if horizon < 1 or horizon > settings.max_forecast_horizon:
            raise HTTPException(400, f"Horizon must be 1-{settings.max_forecast_horizon}")
            
        filename = getattr(file, "filename", "").lower()
        if not (filename.endswith(".csv") or filename.endswith(".xlsx") or filename.endswith(".xls")):
            raise HTTPException(400, "Invalid format. Please upload a CSV or Excel file.")

        contents = await file.read()
        try:
            if filename.endswith(".csv"):
                df = pd.read_csv(io.BytesIO(contents))
            else:
                df = pd.read_excel(io.BytesIO(contents))
        except Exception as e:
            raise HTTPException(400, f"Failed to read file: {e}")
            
        if df.empty:
            raise HTTPException(400, "Uploaded file is empty")

        try:
            monthly_df = prepare_category_data(df=df, category=category, date_col=date_col, category_col=category_col, units_col=units_col, time_grouping=time_grouping)
        except ValueError as ve:
            raise HTTPException(400, str(ve))

        data_months = len(monthly_df)
        validation = validate_forecast_horizon(data_months, horizon)
        if not validation["valid"]:
            raise HTTPException(400, validation["message"])

        data_summary = get_data_summary(monthly_df)
        try:
            forecast_result = run_demand_forecast(monthly_df=monthly_df, periods=horizon)
        except ValueError as ve:
            raise HTTPException(400, str(ve))

        next_month = monthly_df["ds"].max() + pd.DateOffset(months=1)
        month_name = next_month.strftime("%B %Y")
        festivals = get_festivals_for_month(next_month.strftime("%B"), country)

        ext = {
            "upcoming_promotion": _str_to_bool(upcoming_promotion),
            "marketing_campaign": _str_to_bool(marketing_campaign),
            "new_product_launch": _str_to_bool(new_product_launch),
            "availability_issues": _str_to_bool(availability_issues),
            "price_change": price_change,
            "supply_chain_disruption": _str_to_bool(supply_chain_disruption),
            "regulatory_changes": _str_to_bool(regulatory_changes),
            "logistics_constraints": _str_to_bool(logistics_constraints),
            "economic_uncertainty": economic_uncertainty,
            "region": region,
        }

        ext_summary = []
        if ext["upcoming_promotion"]: ext_summary.append("Upcoming promotion planned")
        if ext["marketing_campaign"]: ext_summary.append("Active marketing campaign")
        if ext["new_product_launch"]: ext_summary.append("New product launch expected")
        if ext["availability_issues"]: ext_summary.append("Availability constraints present")
        if ext["price_change"] != "Same": ext_summary.append(f"Price change: {ext['price_change']}")
        if ext["supply_chain_disruption"]: ext_summary.append("Supply chain risk identified")
        if ext["regulatory_changes"]: ext_summary.append("Regulatory changes expected")
        if ext["logistics_constraints"]: ext_summary.append("Logistics constraints present")
        if ext["economic_uncertainty"] != "None": ext_summary.append(f"Economic uncertainty: {ext['economic_uncertainty']}")

        warnings = forecast_result.get("warnings", []).copy()
        if ext["availability_issues"]: warnings.append("Availability constraints may limit demand fulfillment")
        if ext["supply_chain_disruption"]: warnings.append("Supply chain disruptions may impact fulfillment")
        if ext["price_change"] == "Increase": warnings.append("Price increase may reduce demand")
        elif ext["price_change"] == "Decrease": warnings.append("Price decrease may drive demand above forecast")
        if ext["economic_uncertainty"] in ["Medium", "High"]:
            warnings.append(f"{ext['economic_uncertainty']} economic uncertainty increases forecast risk")

        ai_insight = generate_ai_insight(
            category=category, forecasted_units=forecast_result["forecasted_units"],
            mom_change=forecast_result["mom_change_percent"], trend=forecast_result["trend"],
            month=month_name, lower_bound=forecast_result.get("lower_bound"),
            upper_bound=forecast_result.get("upper_bound"), historical_avg=forecast_result.get("historical_avg"),
            yoy_change=forecast_result.get("yoy_change_percent"), data_months=forecast_result.get("data_months"),
            confidence=forecast_result.get("confidence"), region=region, festivals=festivals,
            seasonality=forecast_result.get("seasonality"), warnings=warnings,
            coefficient_of_variation=forecast_result.get("coefficient_of_variation"),
            external_factors=ext, country=country,
        )

        # Trigger background task to generate real Gemini insight
        background_tasks.add_task(
            generate_and_store_insight,
            db=db,
            entity_type="FORECAST",
            entity_id=f"{category}_{month_name.replace(' ', '_')}",
            insight_type="FORECAST_INSIGHT"
        )

        return {
            **forecast_result, "ai_insight": ai_insight, "data_summary": data_summary,
            "forecast_month": month_name, "festivals": festivals, "external_factors": ext_summary,
            "region": region, "country": country,
            "data_quality_message": forecast_result.get("data_quality_message"),
            "warnings": warnings, "recommendations": forecast_result.get("recommendations", []),
        }
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"Server error during forecast: {e}")


@router.post("/forecast/evaluate")
async def evaluate_model(
    file: UploadFile, category: str = Form(...),
    date_col: str = Form(...), category_col: str = Form(...),
    units_col: str = Form(...), holdout_months: int = Form(3),
):
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        monthly_df = prepare_category_data(df=df, category=category, date_col=date_col, category_col=category_col, units_col=units_col)
        if len(monthly_df) < holdout_months + settings.min_months_for_analysis:
            raise HTTPException(400, f"Need at least {holdout_months + settings.min_months_for_analysis} months")
        return {
            "category": category,
            "evaluation": evaluate_forecast_accuracy(monthly_df=monthly_df, holdout_months=holdout_months),
            "diagnostics": get_model_diagnostics(monthly_df),
        }
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"Server error: {e}")


@router.post("/data/summary")
async def get_data_info(
    file: UploadFile, category: str = Form(...),
    date_col: str = Form(...), category_col: str = Form(...), units_col: str = Form(...),
):
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        monthly_df = prepare_category_data(df=df, category=category, date_col=date_col, category_col=category_col, units_col=units_col)
        summary = get_data_summary(monthly_df)
        diagnostics = get_model_diagnostics(monthly_df)
        data_months = len(monthly_df)

        if data_months >= settings.optimal_months:
            readiness, message = "optimal", "Excellent data quality - ready for highly accurate forecasting"
        elif data_months >= settings.min_months_for_seasonality:
            readiness, message = "good", "Good data quality - ready for seasonal forecasting"
        elif data_months >= settings.min_months_for_analysis:
            readiness, message = "limited", "Limited data - forecast will be trend-based only"
        else:
            readiness, message = "insufficient", f"Insufficient data - need {settings.min_months_for_analysis} months"

        return {
            "category": category, "summary": summary, "diagnostics": diagnostics,
            "readiness": readiness, "readiness_message": message,
            "ready_for_forecast": data_months >= settings.min_months_for_analysis,
            "can_detect_seasonality": data_months >= settings.min_months_for_seasonality,
        }
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"Server error: {e}")

# anything
