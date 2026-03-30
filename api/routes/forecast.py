"""
Forecasting routes — /forecast/*, /validate-data, /data/summary
These remain mostly unchanged as they use dedicated external modules.
"""
import io
import traceback
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, Form, BackgroundTasks
from sqlalchemy.orm import Session
import database
from config import settings, get_festivals_for_month, validate_forecast_horizon
from data_preparation import prepare_category_data, get_data_summary
from forecast_service import run_demand_forecast
from ai_insight_service import generate_ai_insight
from evaluation import evaluate_forecast_accuracy, get_model_diagnostics
from services.background_tasks import generate_and_store_insight

router = APIRouter(tags=["Forecasting"])


def _str_to_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in ("true", "1", "yes", "on")


@router.post("/validate-data")
async def validate_data(
    file: UploadFile, category: str = Form(...),
    date_col: str = Form(...), category_col: str = Form(...), units_col: str = Form(...),
):
    try:
        contents = await file.read()
        try:
            df = pd.read_csv(io.BytesIO(contents))
        except Exception as csv_error:
            raise HTTPException(400, f"Failed to read CSV: {csv_error}")
        if df.empty:
            raise HTTPException(400, "Uploaded CSV is empty.")

        missing = [name for col, name in [(date_col, "Date"), (category_col, "Category"), (units_col, "Units")] if col not in df.columns]
        if missing:
            raise HTTPException(400, f"Missing columns: {', '.join(missing)}. Available: {', '.join(df.columns.tolist())}")

        try:
            monthly_df = prepare_category_data(df=df, category=category, date_col=date_col, category_col=category_col, units_col=units_col)
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
        contents = await file.read()
        try:
            df = pd.read_csv(io.BytesIO(contents))
        except Exception as e:
            raise HTTPException(400, f"Failed to read CSV: {e}")
        if df.empty:
            raise HTTPException(400, "Uploaded CSV is empty")

        try:
            monthly_df = prepare_category_data(df=df, category=category, date_col=date_col, category_col=category_col, units_col=units_col)
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
