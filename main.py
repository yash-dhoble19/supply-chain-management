"""
ChainMind Supply Intelligence - Application Entry Point
======================================================
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import database
import models
from api.routes import ai, dashboard, forecast, forecast_ai, inventory, logistics, orders, procurement, products
from config import settings
from services.logistics_tracker import realtime_manager


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Adaptive AI-powered supply chain intelligence platform",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router)
app.include_router(products.router)
app.include_router(procurement.router)
app.include_router(orders.router)
app.include_router(logistics.router)
app.include_router(ai.router)
app.include_router(inventory.router)
app.include_router(forecast_ai.router)
app.include_router(forecast.router)


@app.on_event("startup")
async def startup_event():
    database.initialize_database()
    await realtime_manager.resume_in_transit_shipments()


@app.get("/")
async def root():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "message": "Supply Chain AI System is Online",
        "features": [
            "Dynamic forecast horizon validation",
            "Multi-country support",
            "External factors analysis",
            "Seasonal pattern detection",
            "AI-powered insights",
        ],
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "min_months_required": settings.min_months_for_analysis,
        "recommended_months": settings.min_months_for_seasonality,
        "optimal_months": settings.optimal_months,
        "ai_model": settings.gemini_model,
        "max_forecast_horizon": settings.max_forecast_horizon,
        "supported_countries": ["IN", "US", "UK"],
    }
