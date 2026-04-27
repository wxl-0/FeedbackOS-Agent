import json
from sqlalchemy.orm import Session
from app.core.llm import call_llm
from app.db.models import AgentStep, PrdDocument


async def review_prd(db: Session, prd_id: int, run_id: int | None = None) -> dict:
    prd = db.get(PrdDocument, prd_id)
    result = await call_llm(db, "Reviewer Agent", "review", {"prd_markdown": prd.prd_markdown}, run_id)
    db.add(AgentStep(
        run_id=run_id,
        agent_name="Reviewer Agent",
        step_name="quality_review",
        tool_name="review_prd",
        input_json=json.dumps({"prd_id": prd_id}, ensure_ascii=False),
        output_json=json.dumps(result, ensure_ascii=False),
        step_summary=f"Reviewer score {result.get('quality_score', 0)}; human review required: {result.get('need_human_review', True)}",
        status="success",
        latency_ms=0,
    ))
    db.commit()
    return result

