import json
from sqlalchemy.orm import Session
from app.core.llm import call_llm, prd_markdown
from app.db.models import FeedbackItem, Opportunity, PrdDocument
from app.vectorstore.milvus_client import vector_client


REQUIRED_PRD_SECTIONS = [
    "## 1. 背景与问题",
    "## 2. 目标用户",
    "## 3. 用户故事",
    "## 4. 需求范围",
    "## 5. 功能流程",
    "## 6. 验收标准",
    "## 7. 埋点指标",
    "## 8. 风险点",
    "## 9. 后续迭代建议",
]


FORBIDDEN_PRD_SECTIONS = ["## 证据引用", "## 指标摘要", "evidence id"]


def is_valid_prd_template(markdown: str) -> bool:
    return all(section in markdown for section in REQUIRED_PRD_SECTIONS) and not any(item in markdown for item in FORBIDDEN_PRD_SECTIONS)


async def generate_prd(db: Session, opportunity_id: int, project_id: int = 1, metric_summary: str = "", conversation_id: str | None = None) -> PrdDocument:
    opp = db.get(Opportunity, opportunity_id)
    evidence_ids = json.loads(opp.evidence_ids_json or "[]")
    items = db.query(FeedbackItem).filter(FeedbackItem.id.in_(evidence_ids)).all() if evidence_ids else []
    evidence = [{"id": i.id, "feedback_text": i.feedback_text[:220]} for i in items]
    opportunity = {
        "title": opp.title,
        "problem_statement": opp.problem_statement,
        "target_user": opp.target_user,
    }
    result = await call_llm(db, "PRD Writer Agent", "prd", {
        "opportunity": opportunity,
        "evidence": evidence,
        "metric_summary": metric_summary,
        "evidence_ids": evidence_ids,
    })
    md = result.get("prd_markdown") or ""
    if not is_valid_prd_template(md):
        md = prd_markdown(opportunity, evidence, metric_summary)
    prd = PrdDocument(project_id=project_id, conversation_id=conversation_id or opp.conversation_id, opportunity_id=opportunity_id, title=opp.title, prd_markdown=md)
    db.add(prd)
    db.commit()
    db.refresh(prd)
    await vector_client.insert_prd_embedding(prd.id, project_id, opportunity_id, md)
    return prd
