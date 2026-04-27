from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.memory import MemoryConfirmRequest
from app.services.memory_service import confirm_memory, get_memory

router = APIRouter(prefix="/api/memory", tags=["memory"])


@router.get("")
def memory(project_id: int = 1, user_id: str = "local_user", db: Session = Depends(get_db)):
    return get_memory(db, project_id, user_id)


@router.post("/confirm")
def confirm(payload: MemoryConfirmRequest, db: Session = Depends(get_db)):
    return confirm_memory(db, payload.memory_id, payload.memory_type, payload.content, payload.confirmed, payload.project_id, payload.user_id)

