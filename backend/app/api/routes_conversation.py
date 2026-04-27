from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import AgentRun, AgentStep, InsightCluster, Opportunity, PrdDocument, UploadedFile
from app.schemas.conversation import ConversationCreateRequest, ConversationMessageRequest
from app.services.evaluation_service import compression_metrics, llm_metrics, overview, quality_metrics, retrieval_metrics
from app.services.file_intake_service import serialize_upload
from app.api.routes_clusters import serialize as serialize_cluster
from app.api.routes_opportunities import serialize as serialize_opportunity
from app.api.routes_prd import serialize as serialize_prd
from app.services.conversation_service import add_message, create_conversation, get_conversation, list_conversations, serialize_conversation, serialize_message
import json

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.post("")
def create(payload: ConversationCreateRequest, db: Session = Depends(get_db)):
    conversation = create_conversation(db, payload.title, payload.project_id)
    return serialize_conversation(conversation)


@router.get("")
def list_all(project_id: int = 1, db: Session = Depends(get_db)):
    return list_conversations(db, project_id)


@router.get("/{conversation_id}")
def detail(conversation_id: str, db: Session = Depends(get_db)):
    data = get_conversation(db, conversation_id)
    if not data:
        raise HTTPException(status_code=404, detail="conversation not found")
    return data


@router.post("/{conversation_id}/messages")
def message(conversation_id: str, payload: ConversationMessageRequest, db: Session = Depends(get_db)):
    return serialize_message(add_message(db, conversation_id, payload.role, payload.content))


@router.get("/{conversation_id}/workspace")
def workspace(conversation_id: str, db: Session = Depends(get_db)):
    conversation = get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="conversation not found")
    files = db.query(UploadedFile).filter_by(conversation_id=conversation_id).order_by(UploadedFile.id.desc()).all()
    clusters = db.query(InsightCluster).filter_by(conversation_id=conversation_id).order_by(InsightCluster.feedback_count.desc()).all()
    opportunities = db.query(Opportunity).filter_by(conversation_id=conversation_id).order_by(Opportunity.priority_score.desc()).all()
    prds = db.query(PrdDocument).filter_by(conversation_id=conversation_id).order_by(PrdDocument.id.desc()).all()
    latest_run = db.query(AgentRun).filter_by(conversation_id=conversation_id).order_by(AgentRun.id.desc()).first()
    steps = []
    reviewer_result = None
    retrieved_feedback = []
    if latest_run:
        step_rows = db.query(AgentStep).filter_by(run_id=latest_run.id).order_by(AgentStep.id).all()
        for step in step_rows:
            output = json.loads(step.output_json or "{}")
            if step.agent_name == "Reviewer Agent":
                reviewer_result = output
            if step.agent_name == "Retrieval Agent":
                retrieved_feedback = output.get("retrieved_feedback", [])
            steps.append({
                "id": step.id,
                "agent_name": step.agent_name,
                "step_name": step.step_name,
                "tool_name": step.tool_name,
                "output": output,
                "step_summary": step.step_summary,
                "status": step.status,
                "latency_ms": step.latency_ms,
                "created_at": step.created_at.isoformat(),
            })
    return {
        "conversation": conversation,
        "files": [serialize_upload(file) for file in files],
        "clusters": [serialize_cluster(cluster) for cluster in clusters],
        "opportunities": [serialize_opportunity(opportunity) for opportunity in opportunities],
        "prds": [serialize_prd(prd) for prd in prds],
        "latest_run": {
            "id": latest_run.id,
            "status": latest_run.status,
            "final_output": latest_run.final_output,
            "created_at": latest_run.created_at.isoformat(),
            "finished_at": latest_run.finished_at.isoformat() if latest_run.finished_at else None,
        } if latest_run else None,
        "steps": steps,
        "retrieved_feedback": retrieved_feedback,
        "reviewer_result": reviewer_result,
        "evaluation": {
            "overview": overview(db, conversation_id=conversation_id),
            "llm": llm_metrics(db, conversation_id=conversation_id),
            "retrieval": retrieval_metrics(db, conversation_id=conversation_id),
            "compression": compression_metrics(db, conversation_id=conversation_id),
            "quality": quality_metrics(db, conversation_id=conversation_id),
        },
    }
