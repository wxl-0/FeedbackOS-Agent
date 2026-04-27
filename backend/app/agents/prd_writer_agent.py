import json
from sqlalchemy.orm import Session
from app.core.llm import prd_markdown
from app.db.models import FeedbackItem, Opportunity, PrdDocument
from app.vectorstore.milvus_client import vector_client


async def generate_prd(db: Session, opportunity_id: int, project_id: int = 1, metric_summary: str = "") -> PrdDocument:
    opp = db.get(Opportunity, opportunity_id)
    evidence_ids = json.loads(opp.evidence_ids_json or "[]")
    items = db.query(FeedbackItem).filter(FeedbackItem.id.in_(evidence_ids)).all() if evidence_ids else []
    evidence = [{"id": i.id, "feedback_text": i.feedback_text[:220]} for i in items]
    md = prd_markdown({
        "title": opp.title,
        "problem_statement": opp.problem_statement,
        "target_user": opp.target_user,
    }, evidence, metric_summary)
    prd = PrdDocument(project_id=project_id, opportunity_id=opportunity_id, title=opp.title, prd_markdown=md)
    db.add(prd)
    db.commit()
    db.refresh(prd)
    await vector_client.insert_prd_embedding(prd.id, project_id, opportunity_id, md)
    return prd

