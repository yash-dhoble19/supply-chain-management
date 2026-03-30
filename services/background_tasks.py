import models
import database
from sqlalchemy.orm import Session
from services import ai_service

def generate_and_store_insight(
    db: Session,
    entity_type: str,
    entity_id: str,
    insight_type: str,
    prompt: str = None,
    address: str = None,
    route_desc: str = None,
    distance_km: float = None,
    duration_min: float = None
):
    """
    Background worker that runs AI generation and stores it in the database.
    """
    insight_content = "AI generation failed."
    
    try:
        if insight_type == "RISK_ANALYSIS" and entity_type == "ORDER":
            insight_content = ai_service.analyze_order_risk(address)
            
        elif insight_type == "ROUTE_RISK" and entity_type == "ROUTE":
            insight_content = ai_service.analyze_route_risk(route_desc, distance_km, duration_min)

        else:
            insight_content = "Unsupported insight type"

        # Check if already exists, then update or create
        existing_insight = db.query(models.AIInsight).filter(
            models.AIInsight.entity_type == entity_type,
            models.AIInsight.entity_id == entity_id,
            models.AIInsight.insight_type == insight_type
        ).first()

        if existing_insight:
            existing_insight.content = insight_content
        else:
            new_insight = models.AIInsight(
                entity_type=entity_type,
                entity_id=entity_id,
                insight_type=insight_type,
                content=insight_content
            )
            db.add(new_insight)
        
        db.commit()
    except Exception as e:
        print(f"Background AI Insight Error: {e}")
