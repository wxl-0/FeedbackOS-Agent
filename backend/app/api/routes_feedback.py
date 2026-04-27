from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import InsightCluster, Opportunity, PrdDocument, UploadedFile
from app.services.feedback_service import dashboard_metrics, list_feedback
import json

router = APIRouter(tags=["feedback"])


@router.get("/api/dashboard")
def dashboard(conversation_id: str | None = None, db: Session = Depends(get_db)):
    base = dashboard_metrics(db, conversation_id=conversation_id)
    cq = db.query(InsightCluster)
    oq = db.query(Opportunity)
    pq = db.query(PrdDocument)
    fq = db.query(UploadedFile)
    if conversation_id:
        cq = cq.filter(InsightCluster.conversation_id == conversation_id)
        oq = oq.filter(Opportunity.conversation_id == conversation_id)
        pq = pq.filter(PrdDocument.conversation_id == conversation_id)
        fq = fq.filter(UploadedFile.conversation_id == conversation_id)
    clusters = cq.order_by(InsightCluster.feedback_count.desc()).limit(5).all()
    opps = oq.all()
    prds = pq.count()
    files = fq.order_by(UploadedFile.id.desc()).limit(5).all()
    base.update({
        "top_clusters": [{"id": c.id, "name": c.cluster_name, "count": c.feedback_count, "negative_ratio": c.negative_ratio} for c in clusters],
        "high_priority_opportunities": sum(1 for o in opps if o.priority_level == "P0"),
        "prd_drafts": prds,
        "priority_distribution": [{"name": p, "value": sum(1 for o in opps if o.priority_level == p)} for p in ["P0", "P1", "P2"]],
        "recent_files": [{"id": f.id, "file_name": f.file_name, "parse_status": f.parse_status, "ingest_status": f.ingest_status, "vector_status": f.vector_status, "detected_data_type": f.detected_data_type} for f in files],
    })
    return base


@router.get("/api/feedback")
def feedback(conversation_id: str | None = None, product_module: str | None = None, sentiment: str | None = None, severity: str | None = None, db: Session = Depends(get_db)):
    return list_feedback(db, conversation_id=conversation_id, product_module=product_module, sentiment=sentiment, severity=severity)
