import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.agents.opportunity_agent import generate_opportunities
from app.db.database import get_db
from app.db.models import Opportunity

router = APIRouter(prefix="/api/opportunities", tags=["opportunities"])


@router.post("/generate")
def generate(db: Session = Depends(get_db)):
    return [serialize(o) for o in generate_opportunities(db)]


@router.get("")
def list_opportunities(db: Session = Depends(get_db)):
    return [serialize(o) for o in db.query(Opportunity).order_by(Opportunity.priority_score.desc()).all()]


def serialize(o):
    return {"id": o.id, "cluster_id": o.cluster_id, "title": o.title, "problem_statement": o.problem_statement, "target_user": o.target_user, "impact_score": o.impact_score, "urgency_score": o.urgency_score, "confidence_score": o.confidence_score, "effort_score": o.effort_score, "strategic_fit_score": o.strategic_fit_score, "priority_score": o.priority_score, "priority_level": o.priority_level, "evidence_ids": json.loads(o.evidence_ids_json or "[]"), "status": o.status}
