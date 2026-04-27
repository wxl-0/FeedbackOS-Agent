import json
from sqlalchemy.orm import Session
from app.core.llm import call_llm
from app.db.models import AgentStep, PrdDocument


REQUIRED_SECTIONS = [
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
FORBIDDEN_SECTIONS = ["## 证据引用", "## 指标摘要", "evidence id", "证据ID"]


def deterministic_review(prd_markdown: str) -> dict:
    completeness = int(sum(1 for section in REQUIRED_SECTIONS if section in prd_markdown) / len(REQUIRED_SECTIONS) * 100)
    forbidden_hits = [item for item in FORBIDDEN_SECTIONS if item in prd_markdown]
    score = max(0, completeness - len(forbidden_hits) * 10)
    return {
        "quality_score": score,
        "prd_completeness_score": completeness,
        "evidence_coverage_score": 100,
        "problems": ([] if completeness == 100 else ["PRD 未覆盖全部 9 个规定章节"]) + ([f"包含禁止内容：{', '.join(forbidden_hits)}"] if forbidden_hits else []),
        "suggestions": ["保持固定 9 章节结构，并确保验收标准可测试、埋点指标可落地。"],
        "hallucination_risk": "low" if score >= 90 else "medium",
        "need_human_review": True,
    }


async def review_prd(db: Session, prd_id: int, run_id: int | None = None) -> dict:
    prd = db.get(PrdDocument, prd_id)
    result = await call_llm(db, "Reviewer Agent", "review", {"prd_markdown": prd.prd_markdown}, run_id)
    fallback = deterministic_review(prd.prd_markdown or "")
    for key, value in fallback.items():
        if key not in result or result.get(key) in (None, "", []):
            result[key] = value
    if int(result.get("quality_score") or 0) <= 0 and fallback["quality_score"] > 0:
        result.update(fallback)
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
