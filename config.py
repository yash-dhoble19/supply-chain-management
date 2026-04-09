# backend/config.py - IMPROVED VERSION
# --------------------------------------------

from pydantic_settings import BaseSettings
from typing import Optional, Dict, List, Union
import json


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Keys
    gemini_api_key: Optional[str] = None
    
    # App Settings
    app_name: str = "Demand Forecasting API"
    app_version: str = "1.0.0"
    debug: Union[bool, str] = False
    api_host: str = "127.0.0.1"  # ← Make configurable
    api_port: int = 8000          # ← Make configurable
    
    # Regional Settings - Make flexible
    default_country: str = "IN"
    default_region: str = "India"
    
    # Data Requirements
    min_months_for_analysis: int = 6
    min_months_for_seasonality: int = 12
    optimal_months: int = 24
    default_forecast_horizon: int = 1
    max_forecast_horizon: int = 6
    
    # Prophet Model Settings
    base_yearly_seasonality: bool = True
    weekly_seasonality: bool = False
    daily_seasonality: bool = False
    base_seasonality_mode: str = "multiplicative"
    base_changepoint_prior_scale: float = 0.05
    limited_data_changepoint_scale: float = 0.01
    sufficient_data_changepoint_scale: float = 0.05
    confidence_interval: float = 0.95  # ← Make configurable
    
    # AI Settings
    gemini_model: str = "gemini-1.5-flash"
    ai_temperature: float = 0.4      # ← Now configurable via .env
    ai_max_tokens: int = 700         # ← Now configurable via .env
    
    # Confidence Thresholds
    excellent_confidence_months: int = 24
    high_confidence_months: int = 18
    medium_confidence_months: int = 12
    low_confidence_months: int = 6
    
    # Trend Detection Thresholds
    trend_strong_up: float = 10.0
    trend_up_threshold: float = 5.0
    trend_down_threshold: float = -5.0
    trend_strong_down: float = -10.0
    
    # Inventory Planning Parameters - Now configurable
    base_safety_buffer_pct: float = 0.20      # 20% default buffer
    low_safety_stock_pct: float = 0.08        # 8% for stable demand
    medium_safety_stock_pct: float = 0.10     # 10% for normal variability
    high_safety_stock_pct: float = 0.12       # 12% for high variability
    
    # External Factor Impact Ranges - Configurable estimates
    promotion_min_uplift: float = 0.20        # 20% min
    promotion_max_uplift: float = 0.35        # 35% max
    price_elasticity_moderate: float = 0.15   # 15% demand change per 10% price change
    
    # Festival lead time (weeks before event)
    festival_preparation_weeks: int = 3       # 2-3 weeks configurable
    
    # Seasonality strength thresholds
    weak_seasonality_threshold: float = 10.0
    moderate_seasonality_threshold: float = 25.0
    strong_seasonality_threshold: float = 50.0
    
    # High variability threshold (Coefficient of Variation)
    high_cv_threshold: float = 40.0
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Global settings instance
settings = Settings()


# ===== FESTIVAL MAPPING - EXTENSIBLE SYSTEM =====

# Default festival data for India
DEFAULT_FESTIVALS_INDIA = {
    "January": [
        "Makar Sankranti (January 14-15)",
        "Republic Day (January 26)",
        "Pongal (January 14-17)"
    ],
    "February": ["Maha Shivaratri (Mid-February)"],
    "March": [
        "Holi (Late February/Early March)",
        "Ugadi (Late March/Early April)"
    ],
    "April": [
        "Ram Navami (Mid-April)",
        "Mahavir Jayanti (Late March/Early April)"
    ],
    "May": [
        "Eid al-Fitr (varies)",
        "Buddha Purnima (April/May Full Moon)"
    ],
    "June": ["Eid al-Adha (varies)"],
    "July": ["Guru Purnima (July Full Moon)"],
    "August": [
        "Independence Day (August 15)",
        "Raksha Bandhan (August Full Moon)",
        "Janmashtami (Late August)"
    ],
    "September": [
        "Ganesh Chaturthi (Late August/Early September)",
        "Onam (Late August/Early September)"
    ],
    "October": [
        "Navratri (September/October)",
        "Dussehra (September/October)",
        "Durga Puja (September/October)",
        "Diwali (October/November)"
    ],
    "November": [
        "Diwali (October/November)",
        "Bhai Dooj (November)",
        "Guru Nanak Jayanti (November Full Moon)"
    ],
    "December": [
        "Christmas (December 25)",
        "New Year Eve (December 31)"
    ]
}

# Support for multiple countries/regions
FESTIVAL_DATA = {
    "IN": DEFAULT_FESTIVALS_INDIA,
    "US": {
        "January": ["New Year's Day", "Martin Luther King Jr. Day"],
        "February": ["Valentine's Day", "Presidents' Day"],
        "March": ["St. Patrick's Day"],
        "April": ["Easter (varies)"],
        "May": ["Memorial Day", "Mother's Day"],
        "June": ["Father's Day"],
        "July": ["Independence Day"],
        "September": ["Labor Day"],
        "October": ["Halloween"],
        "November": ["Thanksgiving", "Black Friday"],
        "December": ["Christmas", "New Year's Eve"]
    },
    "UK": {
        "January": ["New Year's Day"],
        "February": ["Valentine's Day"],
        "March": ["Mother's Day (UK)"],
        "April": ["Easter (varies)"],
        "May": ["May Day", "Spring Bank Holiday"],
        "June": ["Father's Day"],
        "August": ["Summer Bank Holiday"],
        "October": ["Halloween"],
        "November": ["Bonfire Night"],
        "December": ["Christmas", "Boxing Day", "New Year's Eve"]
    }
}


def get_festivals_for_month(month_name: str, country: str = None) -> List[str]:
    """
    Get festivals for a given month and country.
    
    Args:
        month_name: Name of the month
        country: ISO country code (default: settings.default_country)
    
    Returns:
        List of festival names
    """
    if country is None:
        country = settings.default_country
    
    country_festivals = FESTIVAL_DATA.get(country, DEFAULT_FESTIVALS_INDIA)
    return country_festivals.get(month_name, [])


def add_custom_festivals(country: str, month: str, festivals: List[str]):
    """
    Add custom festivals for a country/month combination.
    Useful for extending the system without code changes.
    
    Args:
        country: ISO country code
        month: Month name
        festivals: List of festival names
    """
    if country not in FESTIVAL_DATA:
        FESTIVAL_DATA[country] = {}
    
    if month not in FESTIVAL_DATA[country]:
        FESTIVAL_DATA[country][month] = []
    
    FESTIVAL_DATA[country][month].extend(festivals)


def validate_forecast_horizon(data_months: int, requested_horizon: int) -> dict:
    """
    Validate if requested forecast horizon is allowed based on available data.
    
    Args:
        data_months: Number of months of historical data
        requested_horizon: Requested forecast horizon in months
        
    Returns:
        dict: Validation result with allowed horizons and messages
    """
    result = {
        "valid": False,
        "allowed_horizons": [],
        "confidence": "None",
        "message": "",
        "warning": None
    }
    
    # Check absolute minimum
    if data_months < settings.min_months_for_analysis:
        result["message"] = f"Insufficient data. Minimum {settings.min_months_for_analysis} months required."
        result["warning"] = "❌ Cannot generate forecast"
        return result
    
    # Determine allowed horizons
    if data_months < settings.min_months_for_seasonality:
        result["allowed_horizons"] = [1]
        result["confidence"] = "Low"
        result["message"] = "Limited data allows 1-month forecast only"
        result["warning"] = "⚠️ Low confidence: Less than 12 months of data"
        
    elif data_months < settings.optimal_months:
        result["allowed_horizons"] = [1, 3]
        result["confidence"] = "Medium"
        result["message"] = "Medium confidence: 1-3 month forecasts available"
        
    else:
        result["allowed_horizons"] = [1, 3, 6]
        result["confidence"] = "High"
        result["message"] = "High confidence: All forecast horizons available"
    
    # Check if requested horizon is valid
    if requested_horizon in result["allowed_horizons"]:
        result["valid"] = True
    else:
        result["valid"] = False
        required_months = settings.min_months_for_seasonality if requested_horizon == 3 else settings.optimal_months
        result["message"] = f"{requested_horizon}-month forecast requires at least {required_months} months of data (you have {data_months})"
    
    return result


def get_data_quality_tier(data_months: int) -> dict:
    """
    Determine data quality tier and provide appropriate messaging.
    
    Returns:
        dict: Quality tier, message, and recommendations
    """
    if data_months >= settings.optimal_months:
        return {
            "tier": "excellent",
            "label": "Excellent",
            "confidence": "Very High",
            "message": "You have excellent historical data for highly accurate forecasting.",
            "enable_yearly_seasonality": True,
            "enable_holidays": True,
            "warning": None
        }
    elif data_months >= settings.high_confidence_months:
        return {
            "tier": "high",
            "label": "High",
            "confidence": "High",
            "message": "You have sufficient data for reliable forecasting with seasonal patterns.",
            "enable_yearly_seasonality": True,
            "enable_holidays": True,
            "warning": None
        }
    elif data_months >= settings.min_months_for_seasonality:
        return {
            "tier": "medium",
            "label": "Medium",
            "confidence": "Medium",
            "message": "You have adequate data for forecasting. 18+ months recommended for better accuracy.",
            "enable_yearly_seasonality": True,
            "enable_holidays": True,
            "warning": "Limited data for robust yearly seasonality detection"
        }
    elif data_months >= settings.min_months_for_analysis:
        return {
            "tier": "low",
            "label": "Low",
            "confidence": "Low",
            "message": "Limited data available. Forecast will be based on trend analysis only.",
            "enable_yearly_seasonality": False,
            "enable_holidays": False,
            "warning": "⚠️ Less than 12 months of data - seasonal patterns cannot be reliably detected"
        }
    else:
        return {
            "tier": "insufficient",
            "label": "Insufficient",
            "confidence": "None",
            "message": "Insufficient data for forecasting.",
            "enable_yearly_seasonality": False,
            "enable_holidays": False,
            "warning": f"❌ Cannot generate forecast: Less than {settings.min_months_for_analysis} months of data"
        }


def get_safety_stock_percentage(coefficient_of_variation: float, has_external_risks: bool = False) -> float:
    """
    Calculate appropriate safety stock percentage based on demand variability.
    
    Args:
        coefficient_of_variation: CV of historical demand (%)
        has_external_risks: Whether external risk factors are present
        
    Returns:
        float: Safety stock percentage (e.g., 0.10 for 10%)
    """
    if coefficient_of_variation > settings.high_cv_threshold:
        base_pct = settings.high_safety_stock_pct
    elif has_external_risks:
        base_pct = settings.medium_safety_stock_pct
    else:
        base_pct = settings.low_safety_stock_pct
    
    return base_pct


def estimate_promotion_impact_range() -> tuple:
    """
    Get configured promotion impact range.
    
    Returns:
        tuple: (min_uplift, max_uplift) as percentages (e.g., 0.20, 0.35)
    """
    return (settings.promotion_min_uplift, settings.promotion_max_uplift)

# anything
