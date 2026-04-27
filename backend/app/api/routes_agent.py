from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.agents.graph import run_agent_workflow
from app.db.database import get_db
from app.db.models import AgentRun, AgentStep
from app.schemas.agent import AgentRunRequest
from app.services.conversation_service import add_message, ensure_conversation
import json

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/run")
async def run(payload: AgentRunRequest, db: Session = Depends(get_db)):
    conversation = ensure_conversation(db, payload.conversation_id, payload.project_id)
    add_message(db, conversation.id, "user", payload.task)
    state = await run_agent_workflow(db, payload.task, payload.project_id, payload.user_id, conversation.id)
    return {"run_id": state["run_id"], "status": "success", "final_output": state.get("final_output"), "reviewer_result": state.get("reviewer_result"), "draft_prd": state.get("draft_prd")}


@router.get("/runs/{run_id}")
def detail(run_id: int, db: Session = Depends(get_db)):
    r = db.get(AgentRun, run_id)
    return {"id": r.id, "project_id": r.project_id, "user_task": r.user_task, "status": r.status, "final_output": r.final_output, "created_at": r.created_at.isoformat(), "finished_at": r.finished_at.isoformat() if r.finished_at else None}


@router.get("/runs/{run_id}/steps")
def steps(run_id: int, db: Session = Depends(get_db)):
    rows = db.query(AgentStep).filter_by(run_id=run_id).order_by(AgentStep.id).all()
    return [{"id": s.id, "agent_name": s.agent_name, "step_name": s.step_name, "tool_name": s.tool_name, "input": json.loads(s.input_json or "{}"), "output": json.loads(s.output_json or "{}"), "step_summary": s.step_summary, "status": s.status, "latency_ms": s.latency_ms, "created_at": s.created_at.isoformat()} for s in rows]
