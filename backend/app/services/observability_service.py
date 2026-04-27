import json
import time
from contextlib import contextmanager
from sqlalchemy.orm import Session
from app.db.models import AgentStep


@contextmanager
def agent_step(db: Session, run_id: int, agent_name: str, step_name: str, tool_name: str | None = None, input_data: dict | None = None):
    start = time.perf_counter()
    output: dict = {}
    status = "success"
    try:
        yield output
    except Exception as exc:
        status = "failed"
        output["error"] = str(exc)
        raise
    finally:
        summary = output.get("step_summary") or output.get("summary") or f"{agent_name} completed {step_name}"
        db.add(AgentStep(
            run_id=run_id,
            agent_name=agent_name,
            step_name=step_name,
            tool_name=tool_name,
            input_json=json.dumps(input_data or {}, ensure_ascii=False),
            output_json=json.dumps(output, ensure_ascii=False, default=str),
            step_summary=summary,
            status=status,
            latency_ms=int((time.perf_counter() - start) * 1000),
        ))
        db.commit()

