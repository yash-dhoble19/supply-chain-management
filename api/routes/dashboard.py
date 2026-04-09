"""
Dashboard routes — /api/dashboard/*
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import database
from services import dashboard_service

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/bootstrap")
def get_dashboard_bootstrap(db: Session = Depends(database.get_db)):
    return {
        "metrics": dashboard_service.get_dashboard_metrics(db),
        "shipments": dashboard_service.get_dashboard_shipments(db),
        "activities": dashboard_service.get_dashboard_activities(db),
        "stats": dashboard_service.get_dashboard_stats(db),
        "overview": dashboard_service.get_dashboard_overview(db),
    }


@router.get("/metrics")
def get_metrics(db: Session = Depends(database.get_db)):
    return dashboard_service.get_dashboard_metrics(db)


@router.get("/shipments")
def get_shipments(db: Session = Depends(database.get_db)):
    return dashboard_service.get_dashboard_shipments(db)


@router.get("/activities")
def get_activities(db: Session = Depends(database.get_db)):
    return dashboard_service.get_dashboard_activities(db)


@router.get("/stats")
def get_stats(db: Session = Depends(database.get_db)):
    return dashboard_service.get_dashboard_stats(db)


@router.get("/overview")
def get_overview(db: Session = Depends(database.get_db)):
    return dashboard_service.get_dashboard_overview(db)

# anything
