import json
import time
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import LlmCall


MODULE_RULES = [
    ("支付", ["支付", "验证码", "付款", "退款", "扣费"]),
    ("AI 回复", ["AI", "回复", "答非所问", "机器人", "模型"]),
    ("新手引导", ["新手", "引导", "不会用", "教程"]),
    ("性能", ["卡", "慢", "加载", "闪退", "崩溃"]),
    ("会员", ["会员", "权益", "收费", "订阅"]),
    ("搜索", ["搜索", "找不到", "模板"]),
    ("登录", ["登录", "注册", "密码", "账号"]),
]


PROMPTS = {
    "feedback_classification": """你是产品反馈分析 Agent。只能基于输入 text 输出 JSON：
{
  "sentiment": "positive|neutral|negative",
  "product_module": "登录|支付|AI 回复|新手引导|性能|会员|搜索|其他",
  "issue_type": "Bug|体验问题|新需求|投诉|咨询",
  "severity": "low|medium|high",
  "summary": "一句话摘要"
}
不要输出 Markdown，不要添加无依据信息。""",
    "review": """你是 PRD Reviewer Agent。只能基于输入 PRD 输出 JSON：
{
  "quality_score": 0-100,
  "prd_completeness_score": 0-100,
  "evidence_coverage_score": 0-100,
  "problems": ["问题"],
  "suggestions": ["建议"],
  "hallucination_risk": "low|medium|high",
  "need_human_review": true
}
重点检查无依据数字、可测试验收标准、指标设计和 PRD 完整度。不要要求 PRD 正文包含“证据引用”章节。""",
    "compression": "你是上下文压缩节点。只基于输入内容输出 JSON：{\"summary\":\"压缩摘要\",\"key_points\":[\"要点\"]}。",
    "prd": """你是 PRD Writer Agent。只能基于输入的 opportunity、metric_summary 和 evidence 生成 PRD。
必须输出 JSON：{"prd_markdown":"完整 Markdown PRD"}。

PRD Markdown 必须且只能包含以下 9 个一级内容章节：
# {机会点标题}

## 1. 背景与问题
## 2. 目标用户
## 3. 用户故事
## 4. 需求范围
## 5. 功能流程
## 6. 验收标准
## 7. 埋点指标
## 8. 风险点
## 9. 后续迭代建议

禁止包含：
- 证据引用章节
- 指标摘要章节
- evidence id
- 额外章节
- 没有依据的具体数字

要求：
- 每个章节都要有实质内容。
- 验收标准必须可测试。
- 埋点指标必须可落地。
- 不要把证据原文或 evidence_id 写入 PRD 正文。""",
    "default": "Return concise valid JSON only. Use only provided evidence.",
}


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 2)


def classify_text(text: str) -> dict[str, Any]:
    module = "其他"
    for name, words in MODULE_RULES:
        if any(word.lower() in text.lower() for word in words):
            module = name
            break
    negative_words = [
        "差", "慢", "失败", "不能", "无法", "崩溃", "投诉", "退款", "答非所问", "卡",
        "收不到", "放弃", "找不到", "无关", "不准", "不好", "不清楚", "忘记", "过期",
        "不太", "没有结果", "扣费", "闪退", "报错", "卡住", "加载"
    ]
    positive_words = ["好", "喜欢", "满意", "顺畅", "方便"]
    sentiment = "negative" if any(w in text for w in negative_words) else "positive" if any(w in text for w in positive_words) else "neutral"
    severity = "high" if any(w in text for w in ["崩溃", "退款", "失败", "无法", "投诉", "放弃购买"]) else "medium" if sentiment == "negative" else "low"
    issue_type = "Bug" if any(w in text for w in ["崩溃", "闪退", "报错", "失败"]) else "新需求" if any(w in text for w in ["希望", "想要", "建议", "能否"]) else "投诉" if sentiment == "negative" else "咨询"
    return {
        "sentiment": sentiment,
        "product_module": module,
        "issue_type": issue_type,
        "severity": severity,
        "summary": (text[:58] + "...") if len(text) > 60 else text,
    }


def prd_markdown(opportunity: dict[str, Any], evidence: list[dict[str, Any]], metric_summary: str = "") -> str:
    title = opportunity.get("title", "产品机会点 PRD")
    metric_line = f"- 结合当前指标趋势校验方案效果：{metric_summary}" if metric_summary else "- 上线后持续观察负面反馈率、任务成功率和客服工单量变化。"
    return f"""# {title}

## 1. 背景与问题
{opportunity.get('problem_statement', '当前用户反馈暴露出明确体验问题，需要通过产品方案降低使用阻力。')}

## 2. 目标用户
{opportunity.get('target_user', '受该问题影响的核心使用用户。')}

## 3. 用户故事
- 作为目标用户，我希望关键流程更清晰稳定，以便顺利完成当前任务。
- 作为产品团队，我希望能识别并跟踪问题改善效果，以便持续优化体验。

## 4. 需求范围
- 包含：问题识别、关键流程优化、必要提示与反馈闭环。
- 不包含：与本机会点无关的全局重构和非核心功能扩展。

## 5. 功能流程
1. 用户进入相关业务流程。
2. 系统在关键节点提供明确状态、错误原因或下一步建议。
3. 用户完成操作后，系统记录结果并更新体验指标。
4. 产品团队根据反馈和指标复盘迭代。

## 6. 验收标准
- 用户在关键路径遇到问题时，可以看到明确且可行动的提示。
- 核心流程的成功、失败和取消状态都有可追踪记录。
- 相关反馈在上线后可以按模块、情绪和严重度继续归因。

## 7. 埋点指标
- problem_exposed_count
- recovery_click_rate
- task_success_rate
- negative_feedback_rate
- support_ticket_rate

## 8. 风险点
- 方案可能无法覆盖所有边缘场景，需要保留人工处理入口。
- 提示过多可能干扰正常用户，需要控制触发条件和展示频率。
{metric_line}

## 9. 后续迭代建议
- 基于上线后的反馈聚类和指标趋势继续细化优化范围。
- 对高频问题建立长期记忆，作为后续需求评审依据。
"""


async def _call_openai_compatible(settings, prompt_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    import httpx

    async with httpx.AsyncClient(timeout=60) as client:
        res = await client.post(
            f"{settings.resolved_base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {settings.llm_api_key}"},
            json={
                "model": settings.resolved_model,
                "messages": [
                    {"role": "system", "content": PROMPTS.get(prompt_type, PROMPTS["default"])},
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
                ],
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
            },
        )
        res.raise_for_status()
        content = res.json()["choices"][0]["message"]["content"]
        return json.loads(content)


def _mock_result(prompt_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    text = payload.get("text") or payload.get("task") or json.dumps(payload, ensure_ascii=False)
    if prompt_type == "review":
        prd = payload.get("prd_markdown", "")
        required = [
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
        completeness = int(sum(1 for item in required if item in prd) / len(required) * 100)
        forbidden = ["## 证据引用", "## 指标摘要", "evidence id", "证据ID"]
        forbidden_hits = [item for item in forbidden if item in prd]
        return {
            "quality_score": max(0, completeness - len(forbidden_hits) * 10),
            "prd_completeness_score": completeness,
            "evidence_coverage_score": 100,
            "problems": ([] if completeness >= 100 else ["PRD 章节不完整，未覆盖全部 9 个规定章节。"]) + ([f"包含禁止内容：{', '.join(forbidden_hits)}"] if forbidden_hits else []),
            "suggestions": ["保持 9 个固定章节，并确保验收标准可测试、埋点指标可落地。"],
            "hallucination_risk": "low" if completeness >= 100 and not forbidden_hits else "medium",
            "need_human_review": True,
        }
    if prompt_type == "compression":
        return {"summary": text[:500], "key_points": text[:500].split("。")[:5]}
    if prompt_type == "prd":
        return {"prd_markdown": prd_markdown(payload.get("opportunity", {}), payload.get("evidence", []), payload.get("metric_summary", ""))}
    return classify_text(text)


async def call_llm(db: Session, agent_name: str, prompt_type: str, payload: dict[str, Any], run_id: int | None = None) -> dict[str, Any]:
    settings = get_settings()
    start = time.perf_counter()
    success = True
    json_ok = True
    error = None
    used_real_llm = settings.real_llm_enabled
    try:
        if used_real_llm:
            result = await _call_openai_compatible(settings, prompt_type, payload)
        else:
            result = _mock_result(prompt_type, payload)
    except Exception as exc:
        success = False
        json_ok = False
        error = str(exc)
        result = _mock_result(prompt_type, payload)

    latency = int((time.perf_counter() - start) * 1000)
    raw_in = json.dumps(payload, ensure_ascii=False)
    raw_out = json.dumps(result, ensure_ascii=False)
    db.add(LlmCall(
        run_id=run_id,
        agent_name=agent_name,
        model_name=settings.resolved_model if used_real_llm else "mock-llm",
        prompt_type=prompt_type,
        input_tokens=estimate_tokens(raw_in),
        output_tokens=estimate_tokens(raw_out),
        latency_ms=latency,
        cost_estimate=0 if not used_real_llm else estimate_tokens(raw_in + raw_out) * 0.000001,
        cache_hit=False,
        success=success,
        json_parse_success=json_ok,
        error_message=error,
    ))
    db.commit()
    return result
