import json
from sqlalchemy.orm import Session
from app.core.context_builder import estimate_tokens
from app.db.models import CompressionLog


def compress_evidence(db: Session, run_id: int | None, feedback: list[dict], topic: str = "反馈证据") -> dict:
    original = json.dumps(feedback, ensure_ascii=False)
    negative = [f for f in feedback if f.get("sentiment_label") == "negative"]
    quotes = [(f.get("feedback_text") or f.get("text") or "")[:120] for f in feedback[:6]]
    summary = {
        "topic": topic,
        "feedback_count": len(feedback),
        "negative_ratio": round(len(negative) / len(feedback), 3) if feedback else 0,
        "top_complaints": quotes[:3],
        "representative_quotes": quotes,
        "evidence_ids": [f.get("id") or f.get("feedback_id") for f in feedback if f.get("id") or f.get("feedback_id")],
    }
    compressed = json.dumps(summary, ensure_ascii=False)
    ot = estimate_tokens(original)
    ct = estimate_tokens(compressed)
    db.add(CompressionLog(run_id=run_id, compression_type="evidence_summary", original_tokens=ot, compressed_tokens=ct, compression_rate=1 - ct / max(1, ot), summary_text=compressed))
    db.commit()
    return summary


def compress_steps(db: Session, run_id: int | None, steps: list[str]) -> str:
    original = "\n".join(steps)
    summary = "；".join(steps[-8:])[:800]
    ot = estimate_tokens(original)
    ct = estimate_tokens(summary)
    db.add(CompressionLog(run_id=run_id, compression_type="step_summary", original_tokens=ot, compressed_tokens=ct, compression_rate=1 - ct / max(1, ot), summary_text=summary))
    db.commit()
    return summary
