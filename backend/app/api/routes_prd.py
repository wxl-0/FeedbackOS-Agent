import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.agents.metric_analyst_agent import analyze_metrics
from app.agents.prd_writer_agent import generate_prd
from app.agents.reviewer_agent import review_prd
from app.db.database import get_db
from app.db.models import PrdDocument
from app.schemas.prd import PrdGenerateRequest

router = APIRouter(prefix="/api/prd", tags=["prd"])


@router.post("/generate")
async def generate(payload: PrdGenerateRequest, db: Session = Depends(get_db)):
    prd = await generate_prd(db, payload.opportunity_id, payload.project_id, analyze_metrics(db, payload.project_id, payload.conversation_id), payload.conversation_id)
    return serialize(prd)


@router.get("/{prd_id}")
def get_prd(prd_id: int, db: Session = Depends(get_db)):
    return serialize(db.get(PrdDocument, prd_id))


@router.get("")
def list_prds(conversation_id: str | None = None, db: Session = Depends(get_db)):
    q = db.query(PrdDocument)
    if conversation_id:
        q = q.filter(PrdDocument.conversation_id == conversation_id)
    return [serialize(p) for p in q.order_by(PrdDocument.id.desc()).all()]


@router.post("/{prd_id}/review")
async def review(prd_id: int, db: Session = Depends(get_db)):
    return await review_prd(db, prd_id)


def serialize(p: PrdDocument):
    return {"id": p.id, "project_id": p.project_id, "conversation_id": p.conversation_id, "opportunity_id": p.opportunity_id, "title": p.title, "version": p.version, "status": p.status, "prd_markdown": p.prd_markdown, "created_at": p.created_at.isoformat(), "updated_at": p.updated_at.isoformat()}
