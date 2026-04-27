import json
from sqlalchemy.orm import Session
from app.db.models import FeedbackItem, InsightCluster, Opportunity


def generate_opportunities(db: Session, project_id: int = 1) -> list[Opportunity]:
    clusters = db.query(InsightCluster).filter_by(project_id=project_id).all()
    opportunities = []
    for c in clusters:
        items = db.query(FeedbackItem).filter_by(project_id=project_id, product_module=c.product_module).limit(20).all()
        evidence_ids = [i.id for i in items]
        impact = min(100, 45 + c.feedback_count * 5)
        urgency = min(100, 40 + c.negative_ratio * 45 + c.severity_score * 5)
        confidence = min(100, 30 + len(evidence_ids) * 8)
        effort = 45 if c.product_module in ["支付", "登录"] else 35
        fit = 78
        score = impact * 0.35 + urgency * 0.25 + confidence * 0.20 + fit * 0.10 - effort * 0.10
        level = "P0" if score >= 70 and evidence_ids else "P1" if score >= 52 else "P2"
        existing = db.query(Opportunity).filter_by(project_id=project_id, cluster_id=c.id).first()
        opp = existing or Opportunity(project_id=project_id, cluster_id=c.id, title=f"优化{c.product_module or '核心'}体验")
        opp.problem_statement = c.cluster_summary
        opp.target_user = "受该模块问题影响的活跃用户"
        opp.impact_score = round(impact, 1)
        opp.urgency_score = round(urgency, 1)
        opp.confidence_score = round(confidence, 1)
        opp.effort_score = effort
        opp.strategic_fit_score = fit
        opp.priority_score = round(score, 1)
        opp.priority_level = level
        opp.evidence_ids_json = json.dumps(evidence_ids, ensure_ascii=False)
        db.add(opp)
        opportunities.append(opp)
    db.commit()
    return opportunities

