# backend/prophet_model.py
# ------------------------
# Responsibility:
# - Adaptive Prophet model that adjusts based on data availability
# - Train and forecast
# - Add holidays and seasonality based on data quality

import pandas as pd
from prophet import Prophet
from typing import Optional
from config import settings, get_data_quality_tier


class DemandProphetModel:
    """
    Adaptive Prophet-based demand forecasting model.
    Automatically adjusts configuration based on available data.
    """
    
    def __init__(
        self,
        data_months: int = None,
        yearly_seasonality: bool = None,
        weekly_seasonality: bool = None,
        daily_seasonality: bool = None,
        seasonality_mode: str = None,
        changepoint_prior_scale: float = None,
        add_country_holidays: str = "IN"
    ):
        """
        Initialize adaptive Prophet model.
        
        Args:
            data_months: Number of months of historical data (for adaptive settings)
            yearly_seasonality: Override yearly seasonality (default: adaptive)
            weekly_seasonality: Enable weekly seasonality
            daily_seasonality: Enable daily seasonality
            seasonality_mode: 'additive' or 'multiplicative'
            changepoint_prior_scale: Flexibility of trend changes
            add_country_holidays: Country code for holidays (e.g., 'IN' for India)
        """
        
        self.data_months = data_months
        self.quality_tier = None
        
        # Determine optimal settings based on data availability
        if data_months is not None:
            self.quality_tier = get_data_quality_tier(data_months)
            
            # Adaptive yearly seasonality
            if yearly_seasonality is None:
                yearly_seasonality = self.quality_tier["enable_yearly_seasonality"]
            
            # Adaptive changepoint detection
            if changepoint_prior_scale is None:
                if data_months < settings.min_months_for_seasonality:
                    # More conservative for limited data
                    changepoint_prior_scale = settings.limited_data_changepoint_scale
                else:
                    changepoint_prior_scale = settings.sufficient_data_changepoint_scale
            
            # Decide whether to add holidays
            self.add_holidays = self.quality_tier["enable_holidays"]
        else:
            # Fallback to defaults if data_months not provided
            yearly_seasonality = yearly_seasonality or settings.base_yearly_seasonality
            changepoint_prior_scale = changepoint_prior_scale or settings.base_changepoint_prior_scale
            self.add_holidays = True
        
        # Initialize Prophet with determined settings
        self.model = Prophet(
            yearly_seasonality=yearly_seasonality,
            weekly_seasonality=weekly_seasonality if weekly_seasonality is not None else settings.weekly_seasonality,
            daily_seasonality=daily_seasonality if daily_seasonality is not None else settings.daily_seasonality,
            seasonality_mode=seasonality_mode or settings.base_seasonality_mode,
            changepoint_prior_scale=changepoint_prior_scale,
            interval_width=0.95  # 95% confidence interval
        )
        
        # Add country holidays if appropriate
        if self.add_holidays and add_country_holidays:
            try:
                self.model.add_country_holidays(country_name=add_country_holidays)
                self.holidays_enabled = True
            except Exception:
                self.holidays_enabled = False
        else:
            self.holidays_enabled = False
        
        self._is_trained = False
        self._training_data = None

    def add_regressor(self, name: str, prior_scale: float = 10.0, mode: str = "additive"):
        """
        Add an external regressor to the model.
        Must be called before training.
        
        Args:
            name: Name of the regressor column
            prior_scale: Flexibility of the regressor
            mode: 'additive' or 'multiplicative'
        """
        if self._is_trained:
            raise ValueError("Cannot add regressors after model is trained.")
        self.model.add_regressor(name, prior_scale=prior_scale, mode=mode)

    def train(self, monthly_df: pd.DataFrame):
        """
        Train the Prophet model on monthly data.
        
        Args:
            monthly_df: DataFrame with 'ds' (date) and 'y' (value) columns
        """
        if len(monthly_df) < settings.min_months_for_analysis:
            raise ValueError(
                f"Need at least {settings.min_months_for_analysis} data points to train. "
                f"Provided: {len(monthly_df)}"
            )
        
        # Update data_months if not set during initialization
        if self.data_months is None:
            self.data_months = len(monthly_df)
            self.quality_tier = get_data_quality_tier(self.data_months)
        
        self.model.fit(monthly_df)
        self._is_trained = True
        self._training_data = monthly_df.copy()

    def forecast(self, periods: int = 1) -> pd.DataFrame:
        """
        Generate forecast for future periods.
        
        Args:
            periods: Number of months to forecast
            
        Returns:
            pd.DataFrame: Forecast results with Date, Forecasted_Units, bounds
        """
        if not self._is_trained:
            raise ValueError("Model must be trained before forecasting.")
        
        if periods > settings.max_forecast_horizon:
            raise ValueError(
                f"Forecast horizon cannot exceed {settings.max_forecast_horizon} months. "
                f"Requested: {periods}"
            )
        
        # Create future dataframe
        future = self.model.make_future_dataframe(periods=periods, freq="MS")
        forecast = self.model.predict(future)

        # Get only the future forecast points (exclude historical)
        last_historical_date = self.model.history_dates.max()
        forecast_future = forecast[forecast["ds"] > last_historical_date].copy()

        # Extract relevant columns
        forecast_df = forecast_future[[
            "ds", "yhat", "yhat_lower", "yhat_upper"
        ]].copy()

        # Enforce non-negative forecasts (units can't be negative)
        for col in ["yhat", "yhat_lower", "yhat_upper"]:
            forecast_df[col] = (
                forecast_df[col]
                .clip(lower=0)
                .round()
                .astype(int)
            )

        # Rename columns for clarity
        forecast_df = forecast_df.rename(columns={
            "ds": "Date",
            "yhat": "Forecasted_Units",
            "yhat_lower": "Lower_Bound",
            "yhat_upper": "Upper_Bound"
        })

        return forecast_df

    def get_components(self) -> Optional[pd.DataFrame]:
        """
        Get the forecast components (trend, seasonality, holidays).
        Useful for analysis and visualization.
        
        Returns:
            pd.DataFrame: Component breakdown or None if not trained
        """
        if not self._is_trained:
            return None
        
        future = self.model.make_future_dataframe(periods=0, freq="MS")
        forecast = self.model.predict(future)
        
        components = ["ds", "trend"]
        if "yearly" in forecast.columns:
            components.append("yearly")
        if "holidays" in forecast.columns:
            components.append("holidays")
            
        return forecast[components]

    def get_seasonality_strength(self) -> dict:
        """
        Calculate the relative strength of seasonal components with improved accuracy.
        
        Returns:
            dict: Seasonality strength metrics with interpretation
        """
        if not self._is_trained:
            return {
                "yearly_seasonality_strength": 0.0,
                "holiday_impact_strength": 0.0,
                "seasonality_detected": False,
                "interpretation": "Model not trained"
            }
        
        future = self.model.make_future_dataframe(periods=0, freq="MS")
        forecast = self.model.predict(future)
        
        # Calculate relative strength as ratio of component variance to total
        total_variance = forecast["yhat"].var()
        
        yearly_strength = 0.0
        holiday_strength = 0.0
        seasonality_detected = False
        
        # Enhanced yearly seasonality calculation
        if "yearly" in forecast.columns and total_variance > 0:
            yearly_variance = forecast["yearly"].var()
            # Use ratio to total forecast variance
            yearly_strength = min(100, (yearly_variance / total_variance) * 100)
            
            # Also check the magnitude of seasonal swings
            yearly_range = forecast["yearly"].max() - forecast["yearly"].min()
            yearly_mean = abs(forecast["yhat"].mean())
            
            if yearly_mean > 0:
                # Calculate seasonal swing as % of mean forecast
                seasonal_swing_pct = (yearly_range / yearly_mean) * 100
                # Use the maximum of variance-based and swing-based measures
                yearly_strength = max(yearly_strength, seasonal_swing_pct)
            
            # Seasonality is "detected" if it explains >10% variance OR has >15% swing
            if yearly_strength > 10:
                seasonality_detected = True
        
        # Enhanced holiday impact calculation
        if "holidays" in forecast.columns and total_variance > 0:
            holiday_variance = forecast["holidays"].var()
            holiday_strength = min(100, (holiday_variance / total_variance) * 100)
            
            # Also check magnitude of holiday effects
            if not forecast["holidays"].isna().all():
                holiday_range = forecast["holidays"].max() - forecast["holidays"].min()
                holiday_mean = abs(forecast["yhat"].mean())
                
                if holiday_mean > 0:
                    holiday_swing_pct = (holiday_range / holiday_mean) * 100
                    holiday_strength = max(holiday_strength, holiday_swing_pct)
        
        # Interpret seasonality strength
        if not seasonality_detected:
            interpretation = "No significant seasonal pattern detected"
        elif yearly_strength > 50:
            interpretation = "Strong seasonal patterns - demand varies significantly throughout the year"
        elif yearly_strength > 25:
            interpretation = "Moderate seasonal patterns - noticeable variation across months"
        elif yearly_strength > 15:
            interpretation = "Weak seasonal patterns - some monthly variation present"
        else:
            interpretation = "Minimal seasonal patterns - demand is relatively stable"
        
        return {
            "yearly_seasonality_strength": round(yearly_strength, 1),
            "holiday_impact_strength": round(holiday_strength, 1),
            "seasonality_detected": seasonality_detected,
            "interpretation": interpretation,
            "holidays_enabled": self.holidays_enabled
        }

    def get_model_info(self) -> dict:
        """
        Get information about the model configuration.
        
        Returns:
            dict: Model configuration and data quality information
        """
        info = {
            "is_trained": self._is_trained,
            "data_months": self.data_months,
            "yearly_seasonality_enabled": self.model.yearly_seasonality,
            "holidays_enabled": self.holidays_enabled,
            "seasonality_mode": self.model.seasonality_mode,
            "changepoint_prior_scale": self.model.changepoint_prior_scale
        }
        
        if self.quality_tier:
            info.update({
                "data_quality_tier": self.quality_tier["tier"],
                "data_quality_label": self.quality_tier["label"],
                "confidence": self.quality_tier["confidence"],
                "warning": self.quality_tier["warning"]
            })
        
        return info

    @property
    def is_trained(self) -> bool:
        """Check if the model has been trained."""
        return self._is_trained
# anything
