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
    "review": """你是 PRD Reviewer Agent。只能基于输入 PRD 和证据引用输出 JSON：
{
  "quality_score": 0-100,
  "prd_completeness_score": 0-100,
  "evidence_coverage_score": 0-100,
  "problems": ["问题"],
  "suggestions": ["建议"],
  "hallucination_risk": "low|medium|high",
  "need_human_review": true
}
重点检查真实 evidence、无依据数字、可测试验收标准、指标设计和 PRD 完整度。""",
    "compression": "你是上下文压缩节点。只基于输入内容输出 JSON：{\"summary\":\"压缩摘要\",\"key_points\":[\"要点\"]}。",
    "prd": "你是 PRD Writer Agent。只基于 opportunity、evidence_summary、metric_summary 和 evidence 输出 JSON：{\"prd_markdown\":\"完整中文 Markdown PRD\"}。",
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
    negative_words = ["差", "慢", "失败", "不能", "无法", "崩溃", "投诉", "退款", "答非所问", "卡"]
    positive_words = ["好", "喜欢", "满意", "顺畅", "方便"]
    sentiment = "negative" if any(w in text for w in negative_words) else "positive" if any(w in text for w in positive_words) else "neutral"
    severity = "high" if any(w in text for w in ["崩溃", "退款", "失败", "无法", "投诉"]) else "medium" if sentiment == "negative" else "low"
    issue_type = "Bug" if any(w in text for w in ["崩溃", "闪退", "报错", "失败"]) else "新需求" if any(w in text for w in ["希望", "想要", "建议", "能否"]) else "投诉" if sentiment == "negative" else "咨询"
    return {
        "sentiment": sentiment,
        "product_module": module,
        "issue_type": issue_type,
        "severity": severity,
        "summary": (text[:58] + "...") if len(text) > 60 else text,
    }


def prd_markdown(opportunity: dict[str, Any], evidence: list[dict[str, Any]], metric_summary: str = "") -> str:
    title = opportunity.get("title", "需求方案")
    evidence_lines = "\n".join([f"- #{e.get('id')}: {e.get('feedback_text') or e.get('text')}" for e in evidence[:6]]) or "- 暂无证据，需补充用户上传数据"
    return f"""# {title}

## 背景与问题
{opportunity.get('problem_statement', '基于已上传反馈识别到明确痛点，需要形成产品改进方案。')}

## 目标用户
{opportunity.get('target_user', '受该问题影响的核心用户')}

## 用户故事
- 作为目标用户，我希望关键流程稳定、清晰、可预期，以便完成核心任务。
- 作为产品团队，我希望用真实反馈追踪问题规模与改进效果。

## 需求范围
- 覆盖问题识别、异常提示、补救路径与结果反馈。
- 不包含与本机会点无直接证据关联的功能扩展。

## 功能流程
1. 用户进入相关模块。
2. 系统识别风险状态并给出明确反馈。
3. 用户根据提示完成操作或进入人工/自助补救。
4. 系统记录埋点并用于后续评估。

## 验收标准
- 引用证据中的主要问题均有对应处理路径。
- 核心流程成功率、完成时长、负面反馈率可被监测。
- 异常状态必须有可测试的提示、重试或兜底方案。

## 埋点指标
- problem_exposed_count
- recovery_click_rate
- task_success_rate
- negative_feedback_rate
- support_ticket_rate

## 风险点
- 证据覆盖不足时不得扩大结论。
- 改动可能影响既有流程，需要灰度与回滚。

## 后续迭代建议
- 先解决高频高严重度场景，再扩展到相邻模块。
- 每周复盘反馈与指标变化。

## 证据引用
{evidence_lines}

## 指标摘要
{metric_summary or '当前未发现可关联指标，建议上传业务指标表增强判断。'}
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
        required = ["背景与问题", "目标用户", "用户故事", "需求范围", "功能流程", "验收标准", "埋点指标", "风险点", "证据引用"]
        completeness = int(sum(1 for item in required if item in prd) / len(required) * 100)
        evidence = 100 if "#" in prd else 40
        return {
            "quality_score": int((completeness + evidence) / 2),
            "prd_completeness_score": completeness,
            "evidence_coverage_score": evidence,
            "problems": [] if evidence >= 80 else ["证据引用不足"],
            "suggestions": ["保持每个结论可追溯到 feedback evidence"],
            "hallucination_risk": "low" if evidence >= 80 else "medium",
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
