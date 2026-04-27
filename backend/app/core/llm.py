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


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 2)


def classify_text(text: str) -> dict[str, Any]:
    module = "其他"
    for name, words in MODULE_RULES:
        if any(w.lower() in text.lower() for w in words):
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


async def call_llm(db: Session, agent_name: str, prompt_type: str, payload: dict[str, Any], run_id: int | None = None) -> dict[str, Any]:
    settings = get_settings()
    start = time.perf_counter()
    success = True
    json_ok = True
    error = None
    result: dict[str, Any]
    try:
        if settings.real_llm_enabled:
            import httpx

            async with httpx.AsyncClient(timeout=40) as client:
                res = await client.post(
                    f"{settings.openai_base_url.rstrip('/')}/chat/completions",
                    headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                    json={
                        "model": settings.openai_model,
                        "messages": [
                            {"role": "system", "content": "Return concise valid JSON only. Use only provided evidence."},
                            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
                        ],
                        "temperature": 0.2,
                    },
                )
                res.raise_for_status()
                content = res.json()["choices"][0]["message"]["content"]
                try:
                    result = json.loads(content)
                except Exception:
                    json_ok = False
                    result = {"text": content}
        else:
            text = payload.get("text") or payload.get("task") or json.dumps(payload, ensure_ascii=False)
            result = classify_text(text)
            if prompt_type == "review":
                prd = payload.get("prd_markdown", "")
                required = ["背景与问题", "目标用户", "用户故事", "需求范围", "功能流程", "验收标准", "埋点指标", "风险点", "证据引用"]
                completeness = int(sum(1 for item in required if item in prd) / len(required) * 100)
                evidence = 100 if "#" in prd else 40
                result = {
                    "quality_score": int((completeness + evidence) / 2),
                    "prd_completeness_score": completeness,
                    "evidence_coverage_score": evidence,
                    "problems": [] if evidence >= 80 else ["证据引用不足"],
                    "suggestions": ["保持每个结论可追溯到 feedback evidence"],
                    "hallucination_risk": "low" if evidence >= 80 else "medium",
                    "need_human_review": True,
                }
            elif prompt_type == "compression":
                result = {"summary": text[:500], "key_points": text[:500].split("。")[:5]}
    except Exception as exc:
        success = False
        json_ok = False
        error = str(exc)
        result = {"error": error}
    latency = int((time.perf_counter() - start) * 1000)
    raw_in = json.dumps(payload, ensure_ascii=False)
    raw_out = json.dumps(result, ensure_ascii=False)
    db.add(LlmCall(
        run_id=run_id,
        agent_name=agent_name,
        model_name=settings.openai_model if settings.real_llm_enabled else "mock-llm",
        prompt_type=prompt_type,
        input_tokens=estimate_tokens(raw_in),
        output_tokens=estimate_tokens(raw_out),
        latency_ms=latency,
        cost_estimate=0 if not settings.real_llm_enabled else estimate_tokens(raw_in + raw_out) * 0.000001,
        cache_hit=False,
        success=success,
        json_parse_success=json_ok,
        error_message=error,
    ))
    db.commit()
    return result

