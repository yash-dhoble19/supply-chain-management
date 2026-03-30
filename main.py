"""
ChainMind Supply Intelligence — Application Entry Point
========================================================
This is the slim app factory. All business logic lives in services/,
all schemas live in schemas/, and all route handlers live in api/routes/.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import models
import database
from config import settings

# ── Route Modules ────────────────────────────────────────────────────
from api.routes import dashboard, products, procurement, orders, logistics, ai, forecast


# ── App Factory ──────────────────────────────────────────────────────

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Adaptive AI-powered supply chain intelligence platform",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Database Init ────────────────────────────────────────────────────
models.Base.metadata.create_all(bind=database.engine)

# ── Register Routers ─────────────────────────────────────────────────
app.include_router(dashboard.router)
app.include_router(products.router)
app.include_router(procurement.router)
app.include_router(orders.router)
app.include_router(logistics.router)
app.include_router(ai.router)
app.include_router(forecast.router)


# ── Health Checks ────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "message": "Supply Chain AI System is Online 🚀",
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
