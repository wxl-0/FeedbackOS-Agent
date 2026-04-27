from typing import Any


TEXT_KEYS = ["feedback", "content", "comment", "review", "text", "问题", "反馈", "评论", "内容", "建议", "原文"]
DATE_KEYS = ["date", "time", "日期", "时间", "event"]
METRIC_KEYS = ["dau", "留存", "转化", "退款", "成功率", "工单", "满意度", "metric", "指标", "value", "数值"]


def detect_schema(columns: list[str], sample_rows: list[dict[str, Any]]) -> dict[str, Any]:
    lower = {c: c.lower() for c in columns}
    mapping: dict[str, str | None] = {
        "feedback_text": None,
        "event_time": None,
        "channel": None,
        "user_segment": None,
        "metric_date": None,
        "metric_name": None,
        "metric_value": None,
        "dimension_name": None,
        "dimension_value": None,
    }
    for col, low in lower.items():
        if not mapping["feedback_text"] and any(k in low or k in col for k in TEXT_KEYS):
            mapping["feedback_text"] = col
        if not mapping["event_time"] and any(k in low or k in col for k in DATE_KEYS):
            mapping["event_time"] = col
        if not mapping["metric_value"] and any(k in low or k in col for k in ["value", "数值", "值"]):
            mapping["metric_value"] = col
        if not mapping["metric_name"] and any(k in low or k in col for k in ["metric", "指标", "name"]):
            mapping["metric_name"] = col
        if "channel" in low or "渠道" in col or "来源" in col:
            mapping["channel"] = col
        if "segment" in low or "人群" in col or "用户" in col:
            mapping["user_segment"] = col
    numeric_cols = []
    for col in columns:
        values = [r.get(col) for r in sample_rows[:20]]
        ok = 0
        for v in values:
            try:
                float(v)
                ok += 1
            except Exception:
                pass
        if values and ok >= max(1, len(values) // 2):
            numeric_cols.append(col)
    if not mapping["metric_value"] and numeric_cols:
        mapping["metric_value"] = numeric_cols[0]
    if not mapping["feedback_text"] and columns:
        longest = max(columns, key=lambda c: sum(len(str(r.get(c, ""))) for r in sample_rows[:20]))
        mapping["feedback_text"] = longest
    metric_hits = sum(1 for c in columns if any(k in c.lower() or k in c for k in METRIC_KEYS))
    data_type = "metric_data" if metric_hits >= 2 or (mapping["metric_value"] and mapping["metric_name"]) else "feedback_data"
    return {"detected_data_type": data_type, "mapping": mapping, "columns": columns}


def detect_text_type(file_name: str, text: str) -> str:
    name = file_name.lower()
    if "prd" in name or "需求" in text[:1000] or "验收标准" in text:
        return "prd_document"
    if "复盘" in text[:1000] or "会议" in text[:1000] or "访谈" in text[:1000]:
        return "interview_note"
    return "interview_note"

