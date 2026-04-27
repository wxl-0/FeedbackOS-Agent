import json
from collections import defaultdict
from sqlalchemy.orm import Session
from app.db.models import FeedbackItem, InsightCluster


def generate_clusters(db: Session, project_id: int = 1, conversation_id: str | None = None) -> list[InsightCluster]:
    q = db.query(FeedbackItem).filter(FeedbackItem.project_id == project_id)
    if conversation_id:
        q = q.filter(FeedbackItem.conversation_id == conversation_id)
    items = q.all()
    groups = defaultdict(list)
    for item in items:
        groups[item.product_module or "其他"].append(item)
    clusters = []
    for module, rows in groups.items():
        if not rows:
            continue
        neg = sum(1 for r in rows if r.sentiment_label == "negative")
        sev = sum({"high": 3, "medium": 2, "low": 1}.get(r.severity_label or "low", 1) for r in rows) / max(1, len(rows))
        quotes = [{"id": r.id, "text": r.feedback_text[:160]} for r in rows[:5]]
        existing_q = db.query(InsightCluster).filter_by(project_id=project_id, product_module=module)
        if conversation_id:
            existing_q = existing_q.filter(InsightCluster.conversation_id == conversation_id)
        existing = existing_q.first()
        cluster = existing or InsightCluster(project_id=project_id, conversation_id=conversation_id, product_module=module, cluster_name=f"{module}体验痛点")
        cluster.cluster_summary = f"{module}相关反馈共 {len(rows)} 条，负面占比 {neg / len(rows):.0%}，主要集中在可用性、稳定性或预期不一致。"
        cluster.feedback_count = len(rows)
        cluster.negative_ratio = neg / len(rows)
        cluster.severity_score = round(sev, 2)
        cluster.trend_score = round(min(1.0, len(rows) / 20), 2)
        cluster.representative_quotes_json = json.dumps(quotes, ensure_ascii=False)
        db.add(cluster)
        clusters.append(cluster)
    db.commit()
    return clusters
