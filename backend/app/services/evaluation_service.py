import json
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.db.models import AgentRun, AgentStep, CompressionLog, LlmCall, Opportunity, PrdDocument, RetrievalLog


def _run_ids(db: Session, project_id: int = 1, conversation_id: str | None = None) -> list[int]:
    q = db.query(AgentRun.id).filter_by(project_id=project_id)
    if conversation_id:
        q = q.filter(AgentRun.conversation_id == conversation_id)
    return [row[0] for row in q.all()]


def overview(db: Session, project_id: int = 1, conversation_id: str | None = None):
    q = db.query(AgentRun).filter_by(project_id=project_id)
    if conversation_id:
        q = q.filter(AgentRun.conversation_id == conversation_id)
    total = q.count()
    success = q.filter(AgentRun.status == "success").count()
    ids = _run_ids(db, project_id, conversation_id)
    steps = db.query(AgentStep).filter(AgentStep.run_id.in_(ids)).count() if ids else 0
    return {
        "agent_run_total": total,
        "agent_run_success_rate": round(success / total, 3) if total else 0,
        "avg_agent_steps": round(steps / total, 2) if total else 0,
        "avg_tool_calls": round(steps / total, 2) if total else 0,
    }


def llm_metrics(db: Session, project_id: int = 1, conversation_id: str | None = None):
    ids = _run_ids(db, project_id, conversation_id)
    q = db.query(LlmCall)
    if conversation_id:
        q = q.filter(LlmCall.run_id.in_(ids)) if ids else q.filter(False)
    rows = q.all()
    total = len(rows)
    return {
        "llm_call_count": total,
        "avg_latency_ms": round(sum(r.latency_ms for r in rows) / total, 1) if total else 0,
        "input_tokens": sum(r.input_tokens for r in rows),
        "output_tokens": sum(r.output_tokens for r in rows),
        "cost_estimate": round(sum(r.cost_estimate for r in rows), 6),
        "cache_hit_rate": round(sum(1 for r in rows if r.cache_hit) / total, 3) if total else 0,
        "json_parse_success_rate": round(sum(1 for r in rows if r.json_parse_success) / total, 3) if total else 0,
    }


def retrieval_metrics(db: Session, project_id: int = 1, conversation_id: str | None = None):
    ids = _run_ids(db, project_id, conversation_id)
    q = db.query(RetrievalLog)
    if conversation_id:
        q = q.filter(RetrievalLog.run_id.in_(ids)) if ids else q.filter(False)
    rows = q.all()
    total = len(rows)
    oq = db.query(Opportunity).filter_by(project_id=project_id)
    if conversation_id:
        oq = oq.filter(Opportunity.conversation_id == conversation_id)
    opps = oq.all()
    covered = sum(1 for o in opps if json.loads(o.evidence_ids_json or "[]"))
    return {
        "retrieval_count": total,
        "avg_top_k_returned": round(sum(r.returned_count for r in rows) / total, 2) if total else 0,
        "avg_similarity": round(sum(r.avg_similarity for r in rows) / total, 3) if total else 0,
        "no_result_rate": round(sum(1 for r in rows if r.no_result) / total, 3) if total else 0,
        "opportunity_evidence_coverage": round(covered / len(opps), 3) if opps else 0,
    }


def compression_metrics(db: Session, project_id: int = 1, conversation_id: str | None = None):
    ids = _run_ids(db, project_id, conversation_id)
    q = db.query(CompressionLog)
    if conversation_id:
        q = q.filter(CompressionLog.run_id.in_(ids)) if ids else q.filter(False)
    rows = q.all()
    total = len(rows)
    type_q = q.with_entities(CompressionLog.compression_type, func.count()).group_by(CompressionLog.compression_type)
    by_type = {k: v for k, v in type_q.all()}
    return {
        "conversation_summary_count": by_type.get("conversation_summary", 0),
        "evidence_summary_count": by_type.get("evidence_summary", 0),
        "step_summary_count": by_type.get("step_summary", 0),
        "avg_original_tokens": round(sum(r.original_tokens for r in rows) / total, 1) if total else 0,
        "avg_compressed_tokens": round(sum(r.compressed_tokens for r in rows) / total, 1) if total else 0,
        "avg_compression_rate": round(sum(r.compression_rate for r in rows) / total, 3) if total else 0,
    }


def quality_metrics(db: Session, project_id: int = 1, conversation_id: str | None = None):
    pq = db.query(PrdDocument).filter_by(project_id=project_id)
    if conversation_id:
        pq = pq.filter(PrdDocument.conversation_id == conversation_id)
    prds = pq.all()
    required = ["背景与问题", "目标用户", "用户故事", "需求范围", "功能流程", "验收标准", "埋点指标", "风险点", "后续迭代建议"]
    scores = [sum(1 for item in required if item in p.prd_markdown) / len(required) * 100 for p in prds]
    ids = _run_ids(db, project_id, conversation_id)
    reviews_q = db.query(AgentStep).filter(AgentStep.agent_name == "Reviewer Agent")
    if conversation_id:
        reviews_q = reviews_q.filter(AgentStep.run_id.in_(ids)) if ids else reviews_q.filter(False)
    reviews = reviews_q.all()
    review_scores = []
    risk = {"low": 0, "medium": 0, "high": 0}
    human = 0
    problems = 0
    for r in reviews:
        try:
            data = json.loads(r.output_json or "{}")
            review_scores.append(data.get("quality_score", 0))
            risk[data.get("hallucination_risk", "medium")] = risk.get(data.get("hallucination_risk", "medium"), 0) + 1
            human += 1 if data.get("need_human_review") else 0
            problems += len(data.get("problems", []))
        except Exception:
            pass
    return {
        "prd_completeness_avg": round(sum(scores) / len(scores), 1) if scores else 0,
        "reviewer_avg_score": round(sum(review_scores) / len(review_scores), 1) if review_scores else 0,
        "hallucination_risk_distribution": risk,
        "human_review_rate": round(human / len(reviews), 3) if reviews else 0,
        "reviewer_blocked_problem_count": problems,
    }
