# backend/evaluation.py
# ---------------------
# Responsibility:
# - Model performance evaluation
# - Backtesting and cross-validation
# - Accuracy metrics calculation

import pandas as pd
import numpy as np
from typing import Optional, Dict
from prophet import Prophet
from prophet.diagnostics import cross_validation, performance_metrics


def calculate_basic_metrics(actual: pd.Series, predicted: pd.Series) -> Dict[str, float]:
    """
    Calculate basic forecast accuracy metrics.
    
    Args:
        actual: Actual values
        predicted: Predicted values
        
    Returns:
        dict: Dictionary of metrics (MAE, RMSE, MAPE)
    """
    if len(actual) != len(predicted):
        raise ValueError("Actual and predicted series must have same length")
    
    if len(actual) == 0:
        return {"mae": 0, "rmse": 0, "mape": 0}
    
    # Mean Absolute Error
    mae = np.mean(np.abs(actual - predicted))
    
    # Root Mean Square Error
    rmse = np.sqrt(np.mean((actual - predicted) ** 2))
    
    # Mean Absolute Percentage Error (handle zeros)
    non_zero_mask = actual != 0
    if non_zero_mask.sum() > 0:
        mape = np.mean(np.abs((actual[non_zero_mask] - predicted[non_zero_mask]) / actual[non_zero_mask])) * 100
    else:
        mape = 0
    
    return {
        "mae": round(float(mae), 2),
        "rmse": round(float(rmse), 2),
        "mape": round(float(mape), 2)
    }


def run_cross_validation(
    monthly_df: pd.DataFrame,
    initial_months: int = 12,
    period_months: int = 1,
    horizon_months: int = 1
) -> Optional[Dict]:
    """
    Run Prophet cross-validation for model evaluation.
    
    Args:
        monthly_df: Historical monthly data with 'ds' and 'y' columns
        initial_months: Initial training period in months
        period_months: Spacing between cutoff dates
        horizon_months: Forecast horizon to evaluate
        
    Returns:
        dict: Cross-validation metrics or None if insufficient data
    """
    
    data_months = len(monthly_df)
    min_required = initial_months + horizon_months + 2
    
    if data_months < min_required:
        return {
            "status": "insufficient_data",
            "message": f"Need at least {min_required} months for cross-validation, have {data_months}",
            "metrics": None
        }
    
    try:
        # Train model
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=False,
            daily_seasonality=False,
            seasonality_mode="multiplicative"
        )
        model.add_country_holidays(country_name='IN')
        model.fit(monthly_df)
        
        # Run cross-validation
        cv_results = cross_validation(
            model,
            initial=f"{initial_months * 30} days",
            period=f"{period_months * 30} days",
            horizon=f"{horizon_months * 30} days"
        )
        
        # Calculate performance metrics
        metrics_df = performance_metrics(cv_results)
        
        # Get average metrics
        avg_metrics = {
            "mae": round(float(metrics_df["mae"].mean()), 2),
            "rmse": round(float(metrics_df["rmse"].mean()), 2),
            "mape": round(float(metrics_df["mape"].mean() * 100), 2),  # Convert to percentage
            "coverage": round(float(metrics_df["coverage"].mean() * 100), 2) if "coverage" in metrics_df else None
        }
        
        return {
            "status": "success",
            "message": f"Cross-validation completed with {len(cv_results)} evaluation points",
            "metrics": avg_metrics,
            "cv_details": {
                "initial_training_months": initial_months,
                "evaluation_points": len(cv_results)
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Cross-validation failed: {str(e)}",
            "metrics": None
        }


def evaluate_forecast_accuracy(
    monthly_df: pd.DataFrame,
    holdout_months: int = 3
) -> Dict:
    """
    Evaluate forecast accuracy using holdout validation.
    
    Args:
        monthly_df: Complete monthly data
        holdout_months: Number of months to hold out for testing
        
    Returns:
        dict: Evaluation results with metrics
    """
    
    if len(monthly_df) < holdout_months + 6:
        return {
            "status": "insufficient_data",
            "message": f"Need at least {holdout_months + 6} months of data",
            "accuracy_score": None
        }
    
    # Split data
    train_df = monthly_df.iloc[:-holdout_months].copy()
    test_df = monthly_df.iloc[-holdout_months:].copy()
    
    try:
        # Train model
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=False,
            daily_seasonality=False,
            seasonality_mode="multiplicative"
        )
        model.add_country_holidays(country_name='IN')
        model.fit(train_df)
        
        # Forecast for holdout period
        future = model.make_future_dataframe(periods=holdout_months, freq="MS")
        forecast = model.predict(future)
        
        # Get predictions for holdout period
        predictions = forecast.iloc[-holdout_months:]["yhat"].values
        actuals = test_df["y"].values
        
        # Calculate metrics
        metrics = calculate_basic_metrics(
            pd.Series(actuals),
            pd.Series(predictions)
        )
        
        # Calculate accuracy score (100 - MAPE, bounded 0-100)
        accuracy_score = max(0, min(100, 100 - metrics["mape"]))
        
        return {
            "status": "success",
            "holdout_months": holdout_months,
            "metrics": metrics,
            "accuracy_score": round(accuracy_score, 1),
            "interpretation": _interpret_accuracy(accuracy_score),
            "predictions": [
                {
                    "date": test_df.iloc[i]["ds"].strftime("%Y-%m-%d"),
                    "actual": int(actuals[i]),
                    "predicted": int(max(0, predictions[i]))
                }
                for i in range(len(actuals))
            ]
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Evaluation failed: {str(e)}",
            "accuracy_score": None
        }


def _interpret_accuracy(score: float) -> str:
    """Interpret accuracy score for business users."""
    if score >= 90:
        return "Excellent - Highly reliable forecast"
    elif score >= 80:
        return "Good - Reliable for planning"
    elif score >= 70:
        return "Moderate - Use with caution"
    elif score >= 60:
        return "Fair - Consider additional factors"
    else:
        return "Low - Significant uncertainty"


def get_model_diagnostics(monthly_df: pd.DataFrame) -> Dict:
    """
    Get comprehensive model diagnostics.
    
    Args:
        monthly_df: Monthly data with 'ds' and 'y' columns
        
    Returns:
        dict: Diagnostic information
    """
    
    data_months = len(monthly_df)
    
    # Basic data statistics
    stats = {
        "data_points": data_months,
        "date_range": {
            "start": monthly_df["ds"].min().strftime("%Y-%m-%d"),
            "end": monthly_df["ds"].max().strftime("%Y-%m-%d")
        },
        "value_stats": {
            "mean": round(float(monthly_df["y"].mean()), 2),
            "std": round(float(monthly_df["y"].std()), 2),
            "min": int(monthly_df["y"].min()),
            "max": int(monthly_df["y"].max()),
            "coefficient_of_variation": round(float(monthly_df["y"].std() / monthly_df["y"].mean() * 100), 1) if monthly_df["y"].mean() > 0 else 0
        }
    }
    
    # Data quality checks
    quality_checks = {
        "has_sufficient_data": data_months >= 12,
        "has_yearly_seasonality_data": data_months >= 24,
        "has_zero_values": (monthly_df["y"] == 0).any(),
        "has_missing_months": False  # Already aggregated by month
    }
    
    # Recommendations
    recommendations = []
    if data_months < 12:
        recommendations.append("Collect at least 12 months of data for seasonal pattern detection")
    if data_months < 24:
        recommendations.append("24+ months of data recommended for robust yearly seasonality")
    if (monthly_df["y"] == 0).sum() > data_months * 0.1:
        recommendations.append("High proportion of zero values may affect forecast accuracy")
    if stats["value_stats"]["coefficient_of_variation"] > 100:
        recommendations.append("High variability in data - forecasts may have wider uncertainty")
    
    return {
        "statistics": stats,
        "quality_checks": quality_checks,
        "recommendations": recommendations,
        "overall_data_quality": "Good" if all(quality_checks.values()) else "Needs Improvement"
    }

# anything
