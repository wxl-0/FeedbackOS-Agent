import json
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.llm import call_llm
from app.db.models import FeedbackItem


async def analyze_feedback_item(db: Session, item: FeedbackItem, run_id: int | None = None) -> FeedbackItem:
    result = await call_llm(db, "Feedback Analyst Agent", "feedback_classification", {"text": item.feedback_text}, run_id)
    item.sentiment_label = result.get("sentiment", "neutral")
    item.product_module = result.get("product_module", "其他")
    item.issue_type = result.get("issue_type", "咨询")
    item.severity_label = result.get("severity", "low")
    item.feedback_summary = result.get("summary", item.feedback_text[:60])
    db.commit()
    db.refresh(item)
    return item


def list_feedback(db: Session, project_id: int = 1, product_module: str | None = None, sentiment: str | None = None, severity: str | None = None):
    q = db.query(FeedbackItem).filter(FeedbackItem.project_id == project_id)
    if product_module:
        q = q.filter(FeedbackItem.product_module == product_module)
    if sentiment:
        q = q.filter(FeedbackItem.sentiment_label == sentiment)
    if severity:
        q = q.filter(FeedbackItem.severity_label == severity)
    return [serialize_feedback(x) for x in q.order_by(FeedbackItem.id.desc()).limit(200).all()]


def serialize_feedback(x: FeedbackItem):
    return {
        "id": x.id, "project_id": x.project_id, "source_type": x.source_type, "channel": x.channel,
        "user_segment": x.user_segment, "feedback_text": x.feedback_text, "feedback_summary": x.feedback_summary,
        "sentiment_label": x.sentiment_label, "severity_label": x.severity_label, "product_module": x.product_module,
        "issue_type": x.issue_type, "event_time": x.event_time, "created_at": x.created_at.isoformat(),
    }


def dashboard_metrics(db: Session, project_id: int = 1):
    total = db.query(FeedbackItem).filter_by(project_id=project_id).count()
    neg = db.query(FeedbackItem).filter_by(project_id=project_id, sentiment_label="negative").count()
    sentiment = db.query(FeedbackItem.sentiment_label, func.count()).filter_by(project_id=project_id).group_by(FeedbackItem.sentiment_label).all()
    modules = db.query(FeedbackItem.product_module, func.count()).filter_by(project_id=project_id).group_by(FeedbackItem.product_module).all()
    return {
        "total_feedback": total,
        "negative_rate": round(neg / total, 3) if total else 0,
        "sentiment_distribution": [{"name": k or "unknown", "value": v} for k, v in sentiment],
        "module_distribution": [{"name": k or "unknown", "value": v} for k, v in modules],
    }

