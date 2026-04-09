# backend/__init__.py
# -------------------
# Package initializer for backend module

from data_preparation import prepare_category_data
from forecast_service import run_demand_forecast
from prophet_model import DemandProphetModel
from ai_insight_service import generate_ai_insight
from config import settings

__all__ = [
    "prepare_category_data",
    "run_demand_forecast", 
    "DemandProphetModel",
    "generate_ai_insight",
    "settings"
]

__version__ = "0.1.0"               

# anything
