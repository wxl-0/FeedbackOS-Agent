from collections import defaultdict
from sqlalchemy.orm import Session
from app.db.models import MetricSnapshot


def analyze_metrics(db: Session, project_id: int = 1, conversation_id: str | None = None) -> str:
    q = db.query(MetricSnapshot).filter_by(project_id=project_id)
    if conversation_id:
        q = q.filter(MetricSnapshot.conversation_id == conversation_id)
    rows = q.order_by(MetricSnapshot.metric_name, MetricSnapshot.metric_date).all()
    if not rows:
        return "未上传业务指标表，当前机会点评估主要依赖反馈证据。"
    groups = defaultdict(list)
    for r in rows:
        groups[r.metric_name].append(r.metric_value)
    summaries = []
    for name, values in groups.items():
        if len(values) >= 2:
            delta = values[-1] - values[0]
            trend = "上升" if delta > 0 else "下降" if delta < 0 else "持平"
            summaries.append(f"{name} {trend}，首末变化 {delta:.2f}")
        else:
            summaries.append(f"{name} 当前值 {values[-1]:.2f}")
    return "；".join(summaries[:8])
