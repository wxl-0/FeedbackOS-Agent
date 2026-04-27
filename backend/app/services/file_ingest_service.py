import json
from pathlib import Path
from sqlalchemy.orm import Session
from app.db.models import DataSource, DocumentChunk, FeedbackItem, MetricSnapshot, UploadedFile
from app.services.file_intake_service import chunk_text, read_table, read_text, serialize_upload
from app.services.feedback_service import analyze_feedback_item
from app.vectorstore.milvus_client import vector_client


async def ingest_file(db: Session, file_id: int) -> dict:
    uploaded = db.get(UploadedFile, file_id)
    if not uploaded:
        raise ValueError("file not found")
    schema = json.loads(uploaded.schema_json or "{}")
    mapping = schema.get("mapping", {})
    path = Path(uploaded.file_path)
    source = DataSource(
        project_id=uploaded.project_id,
        uploaded_file_id=uploaded.id,
        source_name=uploaded.file_name,
        source_type=uploaded.detected_data_type,
        file_name=uploaded.file_name,
        row_count=uploaded.row_count or uploaded.chunk_count,
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    try:
        if uploaded.detected_data_type == "feedback_data":
            df = read_table(path).fillna("")
            for _, row in df.iterrows():
                text_col = mapping.get("feedback_text")
                text = str(row.get(text_col, "") if text_col else " ".join(map(str, row.values))).strip()
                if not text:
                    continue
                item = FeedbackItem(
                    project_id=uploaded.project_id,
                    data_source_id=source.id,
                    source_type=uploaded.detected_data_type,
                    channel=str(row.get(mapping.get("channel"), ""))[:80] if mapping.get("channel") else None,
                    user_segment=str(row.get(mapping.get("user_segment"), ""))[:120] if mapping.get("user_segment") else None,
                    feedback_text=text,
                    event_time=str(row.get(mapping.get("event_time"), ""))[:80] if mapping.get("event_time") else None,
                )
                db.add(item)
                db.commit()
                db.refresh(item)
                await analyze_feedback_item(db, item)
                await vector_client.insert_feedback_embedding(item.id, item.project_id, f"{item.feedback_text}\n{item.feedback_summary or ''}", {
                    "product_module": item.product_module, "sentiment_label": item.sentiment_label,
                    "source_type": item.source_type, "event_time": item.event_time,
                })
        elif uploaded.detected_data_type == "metric_data":
            df = read_table(path).fillna("")
            for _, row in df.iterrows():
                val = row.get(mapping.get("metric_value")) if mapping.get("metric_value") else None
                try:
                    val = float(val)
                except Exception:
                    continue
                db.add(MetricSnapshot(
                    project_id=uploaded.project_id,
                    data_source_id=source.id,
                    metric_date=str(row.get(mapping.get("event_time") or mapping.get("metric_date"), ""))[:80],
                    metric_name=str(row.get(mapping.get("metric_name"), "metric"))[:120],
                    metric_value=val,
                    dimension_name=str(mapping.get("dimension_name") or "")[:120] or None,
                    dimension_value=str(row.get(mapping.get("dimension_value"), ""))[:120] if mapping.get("dimension_value") else None,
                ))
            db.commit()
        else:
            text = read_text(path)
            chunks = chunk_text(text)
            for chunk in chunks:
                c = DocumentChunk(
                    project_id=uploaded.project_id,
                    uploaded_file_id=uploaded.id,
                    chunk_type=uploaded.detected_data_type,
                    chunk_text=chunk,
                    chunk_summary=chunk[:120],
                    source_title=uploaded.file_name,
                )
                db.add(c)
                db.commit()
                db.refresh(c)
                await vector_client.insert_document_embedding(c.id, c.project_id, uploaded.id, chunk, {"chunk_type": c.chunk_type})
                if any(w in chunk for w in ["痛", "问题", "希望", "建议", "不好", "慢", "失败"]):
                    item = FeedbackItem(project_id=uploaded.project_id, data_source_id=source.id, source_type=uploaded.detected_data_type, feedback_text=chunk[:1200])
                    db.add(item)
                    db.commit()
                    db.refresh(item)
                    await analyze_feedback_item(db, item)
                    await vector_client.insert_feedback_embedding(item.id, item.project_id, item.feedback_text, {
                        "product_module": item.product_module, "sentiment_label": item.sentiment_label, "source_type": item.source_type, "event_time": None,
                    })
        uploaded.ingest_status = "ingested"
        uploaded.vector_status = "completed" if uploaded.detected_data_type != "metric_data" else "skipped"
    except Exception as exc:
        uploaded.ingest_status = "failed"
        uploaded.vector_status = "failed"
        uploaded.error_message = str(exc)
    db.commit()
    return serialize_upload(uploaded)
