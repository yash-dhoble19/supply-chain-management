# backend/forecast_service.py
# ---------------------------
# Responsibility:
# - Adaptive forecasting based on data quality
# - Run forecasting model with appropriate warnings
# - Calculate comprehensive metrics

import pandas as pd
from prophet_model import DemandProphetModel
from config import settings, get_data_quality_tier


def calculate_trend(mom_change: float) -> str:
    """
    Determine trend direction based on month-over-month change.
    
    Args:
        mom_change: Percentage change from last month
        
    Returns:
        str: 'Strong Up', 'Up', 'Down', 'Strong Down', or 'Stable'
    """
    if mom_change >= settings.trend_strong_up:
        return "Strong Up"
    elif mom_change > settings.trend_up_threshold:
        return "Up"
    elif mom_change <= settings.trend_strong_down:
        return "Strong Down"
    elif mom_change < settings.trend_down_threshold:
        return "Down"
    return "Stable"


def calculate_confidence(months: int) -> str:
    """
    Determine forecast confidence based on historical data length.
    
    Args:
        months: Number of months of historical data
        
    Returns:
        str: 'Excellent', 'High', 'Medium', 'Low', or 'Very Low'
    """
    if months >= settings.excellent_confidence_months:
        return "Excellent"
    elif months >= settings.high_confidence_months:
        return "High"
    elif months >= settings.medium_confidence_months:
        return "Medium"
    elif months >= settings.low_confidence_months:
        return "Low"
    return "Very Low"


def calculate_yoy_change(monthly_df: pd.DataFrame, forecasted_units: int) -> float:
    """
    Calculate Year-over-Year change if sufficient data exists.
    
    Args:
        monthly_df: Historical monthly data
        forecasted_units: Forecasted units for next month
        
    Returns:
        float: YoY percentage change or None if insufficient data
    """
    if len(monthly_df) < 12:
        return None
    
    # Get the same month from last year
    last_date = monthly_df["ds"].max()
    same_month_last_year = last_date - pd.DateOffset(months=12)
    
    # Find closest matching month (within 15 days)
    historical = monthly_df[
        (monthly_df["ds"] >= same_month_last_year - pd.Timedelta(days=15)) &
        (monthly_df["ds"] <= same_month_last_year + pd.Timedelta(days=15))
    ]
    
    if historical.empty:
        return None
    
    last_year_value = historical["y"].iloc[0]
    
    if last_year_value > 0:
        return round(((forecasted_units - last_year_value) / last_year_value) * 100, 2)
    
    return None


def run_demand_forecast(
    monthly_df: pd.DataFrame,
    periods: int = 1
) -> dict:
    """
    Run adaptive demand forecasting with comprehensive validation.
    
    Args:
        monthly_df: Pre-aggregated monthly data with 'ds' and 'y' columns
        periods: Number of months to forecast (default: 1)
        
    Returns:
        dict: Complete forecast results including metrics, warnings, and data quality info
        
    Raises:
        ValueError: If data is completely insufficient (< 2 months)
    """

    data_months = len(monthly_df)

    # 1️⃣ DATA QUALITY ASSESSMENT
    quality_info = get_data_quality_tier(data_months)
    
    # Absolute minimum check
    if data_months < settings.min_months_for_analysis:
        raise ValueError(
            f"❌ INSUFFICIENT DATA: Only {data_months} month(s) of data available.\n\n"
            f"Minimum requirement: {settings.min_months_for_analysis} months\n"
            f"Recommended: {settings.min_months_for_seasonality}+ months for seasonal pattern detection\n"
            f"Optimal: {settings.optimal_months}+ months for highly accurate forecasting\n\n"
            "Please upload more historical sales data to generate a forecast."
        )

    # 2️⃣ Initialize ADAPTIVE Prophet model
    model = DemandProphetModel(data_months=data_months)
    model.train(monthly_df)
    
    # Get model configuration info
    model_info = model.get_model_info()
    
    # 3️⃣ Generate forecast
    forecast_df = model.forecast(periods)

    # 4️⃣ Calculate metrics
    last_actual = monthly_df["y"].iloc[-1]
    next_forecast = forecast_df["Forecasted_Units"].iloc[0]
    
    # Month-over-month change (compared to last actual month)
    if last_actual > 0:
        mom_change = ((next_forecast - last_actual) / last_actual) * 100
    else:
        mom_change = 0.0

    trend = calculate_trend(mom_change)
    confidence = calculate_confidence(data_months)
    
    # Total forecasted across all periods
    total_horizon_units = int(forecast_df["Forecasted_Units"].sum())
    
    # Historical statistics for context
    historical_avg = float(monthly_df["y"].mean())
    historical_std = float(monthly_df["y"].std())
    coefficient_of_variation = (historical_std / historical_avg * 100) if historical_avg > 0 else 0
    
    # Year-over-year comparison (if data available)
    yoy_change = calculate_yoy_change(monthly_df, next_forecast)
    
    # Get seasonality insights from model
    seasonality_info = model.get_seasonality_strength()

    # 5️⃣ Prepare output data for plotting
    history_for_plot = (
        monthly_df
        .rename(columns={"ds": "Date", "y": "Actual_Units"})
        .to_dict(orient="records")
    )
    
    # Convert dates to string for JSON serialization
    for record in history_for_plot:
        record["Date"] = record["Date"].strftime("%Y-%m-%d")
    
    forecast_for_plot = forecast_df.to_dict(orient="records")
    for record in forecast_for_plot:
        record["Date"] = record["Date"].strftime("%Y-%m-%d")

    # 6️⃣ Compile warnings and recommendations
    warnings = []
    recommendations = []
    
    if quality_info["warning"]:
        warnings.append(quality_info["warning"])
    
    if data_months < settings.min_months_for_seasonality:
        warnings.append(
            f"⚠️ Only {data_months} months of data available. "
            "Seasonal patterns cannot be detected. Forecast is based on trend only."
        )
        recommendations.append("Collect at least 12 months of historical data to capture yearly seasonal patterns")
    elif data_months < settings.high_confidence_months:
        recommendations.append("Collect 18-24 months of data for more reliable seasonal forecasting")
    
    if coefficient_of_variation > 50:
        warnings.append("⚠️ High variability in historical data detected - forecast uncertainty may be higher")
        recommendations.append("Monitor actuals closely and adjust forecast as new data becomes available")
    
    if not seasonality_info["seasonality_detected"] and data_months >= settings.min_months_for_seasonality:
        recommendations.append("No strong seasonal patterns detected - demand appears relatively stable throughout the year")

    # 7️⃣ Return comprehensive response
    return {
        # === PRIMARY FORECAST DATA ===
        "forecasted_units": int(next_forecast),
        "total_horizon_units": total_horizon_units,
        "forecast_horizon_months": periods,
        
        # === CHANGE METRICS ===
        "mom_change_percent": round(mom_change, 2),
        "yoy_change_percent": yoy_change,
        "trend": trend,
        "confidence": confidence,
        
        # === DATA CONTEXT ===
        "data_months": data_months,
        "historical_avg": round(historical_avg, 2),
        "historical_std": round(historical_std, 2),
        "coefficient_of_variation": round(coefficient_of_variation, 1),
        "last_actual_units": int(last_actual),
        
        # === SEASONALITY INSIGHTS ===
        "seasonality": seasonality_info,
        
        # === CONFIDENCE INTERVAL ===
        "lower_bound": int(forecast_df["Lower_Bound"].iloc[0]),
        "upper_bound": int(forecast_df["Upper_Bound"].iloc[0]),
        "confidence_interval_width": int(forecast_df["Upper_Bound"].iloc[0] - forecast_df["Lower_Bound"].iloc[0]),
        
        # === DATA QUALITY INFO ===
        "data_quality": quality_info["tier"],
        "data_quality_label": quality_info["label"],
        "data_quality_message": quality_info["message"],
        
        # === MODEL INFO ===
        "model_config": {
            "yearly_seasonality_enabled": model_info["yearly_seasonality_enabled"],
            "holidays_enabled": model_info["holidays_enabled"],
            "seasonality_mode": model_info["seasonality_mode"]
        },
        
        # === WARNINGS & RECOMMENDATIONS ===
        "warnings": warnings,
        "recommendations": recommendations,
        
        # === PLOT DATA ===
        "history_data": history_for_plot,
        "forecast_data": forecast_for_plot
    }
# anything
