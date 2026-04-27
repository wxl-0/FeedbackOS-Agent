import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.agents.cluster_agent import generate_clusters
from app.db.database import get_db
from app.db.models import InsightCluster

router = APIRouter(prefix="/api/clusters", tags=["clusters"])


@router.post("/generate")
def generate(conversation_id: str, db: Session = Depends(get_db)):
    return [serialize(c) for c in generate_clusters(db, conversation_id=conversation_id)]


@router.get("")
def list_clusters(conversation_id: str | None = None, db: Session = Depends(get_db)):
    q = db.query(InsightCluster)
    if conversation_id:
        q = q.filter(InsightCluster.conversation_id == conversation_id)
    return [serialize(c) for c in q.order_by(InsightCluster.feedback_count.desc()).all()]


def serialize(c):
    return {"id": c.id, "cluster_name": c.cluster_name, "cluster_summary": c.cluster_summary, "product_module": c.product_module, "feedback_count": c.feedback_count, "negative_ratio": c.negative_ratio, "severity_score": c.severity_score, "trend_score": c.trend_score, "representative_quotes": json.loads(c.representative_quotes_json or "[]"), "status": c.status}
