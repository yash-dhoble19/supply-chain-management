"""
AI feature routes — /ai/*
"""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import database
from schemas.ai import (
    AIProductParseRequest, PricingRequest, InventoryReportRequest,
    SimulationRequest, ReorderRequest, AgentRouteRequest,
)
from services import ai_service
from ai_agent import SupplyChainAgent

router = APIRouter(prefix="/ai", tags=["AI Features"])


@router.post("/pricing_analysis")
def analyze_pricing(req: PricingRequest):
    ratio = req.current_stock / req.optimal_stock if req.optimal_stock > 0 else 0
    try:
        return ai_service.analyze_pricing(req.product_name, req.current_price, ratio)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parse_product_info")
def parse_product_info(request: AIProductParseRequest):
    if not request.description or request.description.strip() == "":
        raise HTTPException(status_code=400, detail="Description cannot be empty")
    return ai_service.parse_product_info(request.description)


@router.post("/audit_inventory")
def audit_inventory(req: InventoryReportRequest):
    try:
        report = ai_service.audit_inventory(req.products)
        return {"report": report}
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simulate_scenario")
def simulate_scenario(req: SimulationRequest):
    context = "\n".join([f"- {p['product']}: Stock {p['on_hand']}" for p in req.products])
    try:
        return ai_service.simulate_scenario(req.scenario, context)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate_reorder_email")
def generate_reorder_email(req: ReorderRequest):
    try:
        return ai_service.draft_negotiation_email(
            req.product_name, req.supplier_name, req.current_stock, req.optimal_stock, req.unit_price,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent/route")
def agent_route(req: AgentRouteRequest):
    return SupplyChainAgent.route(req.intent, req.payload)
