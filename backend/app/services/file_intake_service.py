import json
import shutil
from pathlib import Path
from typing import Any
import pandas as pd
from docx import Document
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.db.models import UploadedFile
from app.services.schema_detection_service import detect_schema, detect_text_type


def safe_name(name: str) -> str:
    return Path(name).name.replace(" ", "_")


async def save_upload(db: Session, file: UploadFile, project_id: int = 1) -> UploadedFile:
    settings = get_settings()
    target = settings.upload_dir / safe_name(file.filename or "upload.bin")
    idx = 1
    while target.exists():
        target = settings.upload_dir / f"{target.stem}_{idx}{target.suffix}"
        idx += 1
    with target.open("wb") as out:
        shutil.copyfileobj(file.file, out)
    item = UploadedFile(
        project_id=project_id,
        file_name=file.filename or target.name,
        file_path=str(target),
        file_type=target.suffix.lower().lstrip("."),
        file_size=target.stat().st_size,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def read_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        try:
            return pd.read_csv(path)
        except UnicodeDecodeError:
            return pd.read_csv(path, encoding="gbk")
    return pd.read_excel(path)


def read_text(path: Path) -> str:
    if path.suffix.lower() == ".docx":
        doc = Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="gbk", errors="ignore")


def chunk_text(text: str, size: int = 900, overlap: int = 120) -> list[str]:
    clean = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    chunks = []
    i = 0
    while i < len(clean):
        chunk = clean[i:i + size].strip()
        if chunk:
            chunks.append(chunk)
        i += size - overlap
    return chunks


def parse_file(db: Session, file_id: int) -> dict[str, Any]:
    uploaded = db.get(UploadedFile, file_id)
    if not uploaded:
        raise ValueError("file not found")
    path = Path(uploaded.file_path)
    try:
        if path.suffix.lower() in [".csv", ".xlsx", ".xls"]:
            df = read_table(path).fillna("")
            rows = df.head(30).to_dict(orient="records")
            schema = detect_schema(list(df.columns), rows)
            uploaded.detected_data_type = schema["detected_data_type"]
            uploaded.row_count = len(df)
            uploaded.schema_json = json.dumps(schema, ensure_ascii=False)
            uploaded.preview_json = json.dumps(rows[:10], ensure_ascii=False, default=str)
        elif path.suffix.lower() in [".txt", ".md", ".docx"]:
            text = read_text(path)
            chunks = chunk_text(text)
            uploaded.detected_data_type = detect_text_type(uploaded.file_name, text)
            uploaded.chunk_count = len(chunks)
            uploaded.schema_json = json.dumps({"mapping": {}, "columns": [], "detected_data_type": uploaded.detected_data_type}, ensure_ascii=False)
            uploaded.preview_json = json.dumps([{"chunk_text": c[:500]} for c in chunks[:8]], ensure_ascii=False)
        else:
            uploaded.detected_data_type = "unknown"
            uploaded.error_message = "Unsupported file type"
        uploaded.parse_status = "parsed" if uploaded.detected_data_type != "unknown" else "failed"
    except Exception as exc:
        uploaded.parse_status = "failed"
        uploaded.error_message = str(exc)
    db.commit()
    db.refresh(uploaded)
    return serialize_upload(uploaded)


def confirm_schema(db: Session, file_id: int, mapping: dict[str, Any]) -> dict[str, Any]:
    uploaded = db.get(UploadedFile, file_id)
    schema = json.loads(uploaded.schema_json or "{}")
    schema["mapping"] = {**schema.get("mapping", {}), **mapping}
    schema["confirmed"] = True
    uploaded.schema_json = json.dumps(schema, ensure_ascii=False)
    db.commit()
    return serialize_upload(uploaded)


def serialize_upload(file: UploadedFile) -> dict[str, Any]:
    return {
        "id": file.id,
        "project_id": file.project_id,
        "file_name": file.file_name,
        "file_type": file.file_type,
        "file_size": file.file_size,
        "detected_data_type": file.detected_data_type,
        "parse_status": file.parse_status,
        "ingest_status": file.ingest_status,
        "vector_status": file.vector_status,
        "row_count": file.row_count,
        "chunk_count": file.chunk_count,
        "schema": json.loads(file.schema_json or "{}"),
        "preview": json.loads(file.preview_json or "[]"),
        "error_message": file.error_message,
        "created_at": file.created_at.isoformat(),
    }

