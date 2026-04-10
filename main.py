"""
ChainMind Supply Intelligence - Application Entry Point
======================================================
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

import database
import models
from api.routes import (
    ai,
    ai_tools,
    auth,
    dashboard,
    drivers,
    forecast,
    forecast_ai,
    inventory,
    logistics,
    logistics_orders,
    manufacturing,
    orders,
    payments,
    procurement,
    products,
    published_goods,
    schedules,
)
from api.auth_handler import get_current_user
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

# --- Auth route (public, no token required) ---
app.include_router(auth.router)

# --- Protected/Public routers mix (simplest method for now) ---
app.include_router(dashboard.router)
app.include_router(products.router)
app.include_router(procurement.router)
app.include_router(orders.router)
app.include_router(logistics.router)
app.include_router(ai.router)
app.include_router(ai_tools.router)
app.include_router(inventory.router)
app.include_router(forecast_ai.router)
app.include_router(forecast.router)

# --- New routers from CodeByAmruta ---
app.include_router(manufacturing.router)
app.include_router(published_goods.router)
app.include_router(logistics_orders.router)
app.include_router(schedules.router)
app.include_router(payments.router)
app.include_router(drivers.router)


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
            "JWT Authentication",
            "Manufacturing Management",
            "Marketplace & Published Goods",
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

# anything
