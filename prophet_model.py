# backend/prophet_model.py
# ------------------------
# Responsibility:
# - Adaptive Prophet model that adjusts based on data availability
# - Train and forecast at both monthly AND daily granularity
# - Add holidays and seasonality based on data quality
# - Single model used for ALL demand types (Smooth, Erratic, Intermittent, Seasonal, New)

import pandas as pd
import numpy as np
from prophet import Prophet
from typing import Optional
from config import settings, get_data_quality_tier


class DemandProphetModel:
    """
    Adaptive Prophet-based demand forecasting model.
    Automatically adjusts configuration based on available data.

    Supports two frequencies:
        - 'MS' (Month Start) — existing monthly forecasting
        - 'D'  (Daily)       — daily-level forecasting for frontend engine

    This model is the SOLE forecasting engine for all demand types.
    Demand classification (Smooth/Erratic/Intermittent/Seasonal/New) is
    purely descriptive and does NOT influence model selection or parameters.
    """

    def __init__(
        self,
        data_months: int = None,
        freq: str = "MS",
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
            data_months: Number of months of historical data (for adaptive settings).
                         For daily data pass None and let train() infer.
            freq: Forecast frequency — 'MS' for monthly, 'D' for daily
            yearly_seasonality: Override yearly seasonality (default: adaptive)
            weekly_seasonality: Enable weekly seasonality (default: adaptive per freq)
            daily_seasonality: Enable daily seasonality
            seasonality_mode: 'additive' or 'multiplicative'
            changepoint_prior_scale: Flexibility of trend changes
            add_country_holidays: Country code for holidays (e.g., 'IN' for India)
        """

        self.data_months = data_months
        self.freq = freq
        self.quality_tier = None

        # --- Adaptive settings based on data months (monthly path) ---
        if data_months is not None:
            self.quality_tier = get_data_quality_tier(data_months)

            if yearly_seasonality is None:
                yearly_seasonality = self.quality_tier["enable_yearly_seasonality"]

            if changepoint_prior_scale is None:
                if data_months < settings.min_months_for_seasonality:
                    changepoint_prior_scale = settings.limited_data_changepoint_scale
                else:
                    changepoint_prior_scale = settings.sufficient_data_changepoint_scale

            self.add_holidays = self.quality_tier["enable_holidays"]

        elif freq == "D":
            # --- Daily path: adaptive defaults based on data length set in train() ---
            if yearly_seasonality is None:
                yearly_seasonality = False          # overridden in train() if enough data
            if weekly_seasonality is None:
                weekly_seasonality = True           # daily data benefits from weekly cycles
            if changepoint_prior_scale is None:
                changepoint_prior_scale = 0.1
            self.add_holidays = True

        else:
            # Fallback defaults (monthly, no data_months given)
            yearly_seasonality = yearly_seasonality or settings.base_yearly_seasonality
            changepoint_prior_scale = changepoint_prior_scale or settings.base_changepoint_prior_scale
            self.add_holidays = True

        # Initialize Prophet with determined settings
        self.model = Prophet(
            yearly_seasonality=yearly_seasonality,
            weekly_seasonality=weekly_seasonality if weekly_seasonality is not None else settings.weekly_seasonality,
            daily_seasonality=daily_seasonality if daily_seasonality is not None else settings.daily_seasonality,
            seasonality_mode=seasonality_mode or "multiplicative",
            changepoint_prior_scale=changepoint_prior_scale,
            seasonality_prior_scale=10.0,
            interval_width=0.50  # 50% confidence interval (prevents excessive lower bound variance)
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
        self._used_log_transform = False

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

    def _preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess training data to handle spiky and unrealistic data points:
        1. Fill missing dates ensuring consistent frequency.
        2. IQR to cap extreme spikes.
        3. Light 3-day or 7-day rolling mean for smoothing.
        4. Log transformation for highly erratic demand.
        """
        df = df.copy()
        
        # 1. Fill missing dates
        df['ds'] = pd.to_datetime(df['ds'])
        df = df.set_index('ds').resample(self.freq).sum().reset_index()
        df['y'] = df['y'].fillna(0)
        
        # 2. Outlier Handling (Cap extreme spikes using IQR)
        Q1 = df['y'].quantile(0.25)
        Q3 = df['y'].quantile(0.75)
        IQR = Q3 - Q1
        upper_bound = Q3 + 1.5 * IQR
        
        if upper_bound > 0:
            df['y'] = np.where(df['y'] > upper_bound, upper_bound, df['y'])
            
        # 3. Light Smoothing
        if self.freq == "D":
            # 7-day rolling mean to smooth out noise without losing trend
            df['y'] = df['y'].rolling(window=7, min_periods=1, center=True).mean()
        
        # 4. Spiky/Erratic demand check (Log Transformation)
        cv = df['y'].std() / df['y'].mean() if df['y'].mean() > 0 else 0
        self._used_log_transform = False
        
        if cv > 1.2:
            self._used_log_transform = True
            # log(1 + y) handles zeroes and smooths out huge fluctuations
            df['y'] = np.log1p(df['y'])
            
        return df

    def train(self, df: pd.DataFrame):
        """
        Train the Prophet model.

        Args:
            df: DataFrame with 'ds' (date) and 'y' (value) columns.
                For monthly data: monthly-aggregated rows.
                For daily data:   daily-aggregated rows.
        """
        df_clean = self._preprocess(df)
        n_rows = len(df_clean)

        if self.freq == "D":
            # Daily path: infer data_months and adapt seasonality
            if n_rows < 2:
                raise ValueError(
                    f"Need at least 2 daily data points to train. Provided: {n_rows}"
                )
            if self.data_months is None:
                self.data_months = max(1, n_rows // 30)
                self.quality_tier = get_data_quality_tier(self.data_months)

            # Enable yearly seasonality if we have ≥365 days
            if n_rows >= 365:
                self.model.yearly_seasonality = True

        else:
            # Monthly path: enforce minimum
            if n_rows < settings.min_months_for_analysis:
                raise ValueError(
                    f"Need at least {settings.min_months_for_analysis} data points to train. "
                    f"Provided: {n_rows}"
                )
            if self.data_months is None:
                self.data_months = n_rows
                self.quality_tier = get_data_quality_tier(self.data_months)

        self.model.fit(df_clean)
        self._is_trained = True
        self._training_data = df_clean.copy()

    def forecast(self, periods: int = 1) -> pd.DataFrame:
        """
        Generate forecast for future periods.

        Args:
            periods: Number of periods to forecast (months if freq='MS', days if freq='D')

        Returns:
            pd.DataFrame: Forecast results with Date, Forecasted_Units, bounds
        """
        if not self._is_trained:
            raise ValueError("Model must be trained before forecasting.")

        # For monthly data, enforce max horizon
        if self.freq == "MS" and periods > settings.max_forecast_horizon:
            raise ValueError(
                f"Forecast horizon cannot exceed {settings.max_forecast_horizon} months. "
                f"Requested: {periods}"
            )

        # Create future dataframe using the model's frequency
        future = self.model.make_future_dataframe(periods=periods, freq=self.freq)
        forecast = self.model.predict(future)

        # Get only the future forecast points (exclude historical)
        last_historical_date = self.model.history_dates.max()
        forecast_future = forecast[forecast["ds"] > last_historical_date].copy()

        # Reverse Log Transform, if applied
        if getattr(self, '_used_log_transform', False):
            for col in ['yhat', 'yhat_lower', 'yhat_upper']:
                forecast_future[col] = np.expm1(forecast_future[col])

        # Extract relevant columns
        forecast_df = forecast_future[[
            "ds", "yhat", "yhat_lower", "yhat_upper"
        ]].copy()

        # Enforce non-negative forecasts and a 80% "Supply Chain Floor" for the lower bound 
        # to ensure it's useful for inventory planning even when variance is high.
        forecast_df["yhat"] = forecast_df["yhat"].clip(lower=0)
        forecast_df["yhat_upper"] = forecast_df["yhat_upper"].clip(lower=0)
        
        # If lower bound is too low/zero, provide a 80% safety floor of the forecast
        forecast_df["yhat_lower"] = np.where(
            forecast_df["yhat_lower"] < (forecast_df["yhat"] * 0.8),
            forecast_df["yhat"] * 0.8,
            forecast_df["yhat_lower"]
        )
        
        for col in ["yhat", "yhat_lower", "yhat_upper"]:
            forecast_df[col] = forecast_df[col].round().astype(int)

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
