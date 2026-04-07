"""
ChainMind Supply Intelligence - Application Entry Point
======================================================
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

import database
import models
from api.routes import ai, auth, dashboard, inventory, logistics, orders, procurement, products, manufacturing, logistics_orders, published_goods
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

secure_depends = [Depends(get_current_user)]

app.include_router(dashboard.router, dependencies=secure_depends)
app.include_router(products.router, dependencies=secure_depends)
app.include_router(procurement.router, dependencies=secure_depends)
app.include_router(orders.router, dependencies=secure_depends)
app.include_router(logistics.router, dependencies=secure_depends)
app.include_router(logistics_orders.router, dependencies=secure_depends)
app.include_router(ai.router, dependencies=secure_depends)
app.include_router(published_goods.router, dependencies=secure_depends)
app.include_router(inventory.router, dependencies=secure_depends)
app.include_router(manufacturing.router, dependencies=secure_depends)
app.include_router(auth.router)


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
