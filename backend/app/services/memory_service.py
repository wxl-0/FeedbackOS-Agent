import json
from sqlalchemy.orm import Session
from app.db.models import DecisionMemory, ProjectMemory, UserPreferenceMemory


def get_memory(db: Session, project_id: int = 1, user_id: str = "local_user"):
    return {
        "project_memory": [serialize_project(m) for m in db.query(ProjectMemory).filter_by(project_id=project_id).order_by(ProjectMemory.id.desc()).all()],
        "decision_memory": [serialize_decision(m) for m in db.query(DecisionMemory).filter_by(project_id=project_id).order_by(DecisionMemory.id.desc()).all()],
        "user_preference_memory": [serialize_pref(m) for m in db.query(UserPreferenceMemory).filter_by(user_id=user_id).order_by(UserPreferenceMemory.id.desc()).all()],
    }


def confirm_memory(db: Session, memory_id: int | None, memory_type: str, content: dict | None, confirmed: bool, project_id: int, user_id: str):
    if memory_id and memory_type == "project":
        item = db.get(ProjectMemory, memory_id)
        item.confirmed_by_user = True
    elif memory_type == "decision":
        item = DecisionMemory(project_id=project_id, decision_title=(content or {}).get("title", "人工确认决策"), decision_content=json.dumps(content or {}, ensure_ascii=False), evidence_json=json.dumps((content or {}).get("evidence", []), ensure_ascii=False), confirmed_by_user=confirmed)
        db.add(item)
    elif memory_type == "preference":
        item = UserPreferenceMemory(user_id=user_id, preference_key=(content or {}).get("key", "prd_style"), preference_value=(content or {}).get("value", ""), confirmed_by_user=confirmed)
        db.add(item)
    else:
        item = ProjectMemory(project_id=project_id, memory_type=memory_type, content_json=json.dumps(content or {}, ensure_ascii=False), source="human", confirmed_by_user=True)
        db.add(item)
    db.commit()
    return {"ok": True}


def serialize_project(m):
    return {"id": m.id, "memory_type": m.memory_type, "content": json.loads(m.content_json), "source": m.source, "confirmed_by_user": m.confirmed_by_user, "created_at": m.created_at.isoformat()}


def serialize_decision(m):
    return {"id": m.id, "decision_title": m.decision_title, "decision_content": m.decision_content, "evidence": json.loads(m.evidence_json or "[]"), "confirmed_by_user": m.confirmed_by_user, "created_at": m.created_at.isoformat()}


def serialize_pref(m):
    return {"id": m.id, "preference_key": m.preference_key, "preference_value": m.preference_value, "confirmed_by_user": m.confirmed_by_user, "created_at": m.created_at.isoformat()}
