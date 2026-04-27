from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import UploadedFile
from app.schemas.upload import ConfirmSchemaRequest
from app.services.file_ingest_service import ingest_file
from app.services.file_intake_service import confirm_schema, parse_file, save_upload, serialize_upload

router = APIRouter(prefix="/api/upload", tags=["upload"])


@router.post("")
async def upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    item = await save_upload(db, file)
    return serialize_upload(item)


@router.get("/files")
def files(db: Session = Depends(get_db)):
    return [serialize_upload(f) for f in db.query(UploadedFile).order_by(UploadedFile.id.desc()).all()]


@router.get("/files/{file_id}")
def file_detail(file_id: int, db: Session = Depends(get_db)):
    return serialize_upload(db.get(UploadedFile, file_id))


@router.post("/files/{file_id}/parse")
def parse(file_id: int, db: Session = Depends(get_db)):
    return parse_file(db, file_id)


@router.post("/files/{file_id}/confirm-schema")
def confirm(file_id: int, payload: ConfirmSchemaRequest, db: Session = Depends(get_db)):
    return confirm_schema(db, file_id, payload.mapping)


@router.post("/files/{file_id}/ingest")
async def ingest(file_id: int, db: Session = Depends(get_db)):
    return await ingest_file(db, file_id)

