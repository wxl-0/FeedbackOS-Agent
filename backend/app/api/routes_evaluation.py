from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.evaluation_service import compression_metrics, llm_metrics, overview, quality_metrics, retrieval_metrics

router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])


@router.get("/overview")
def eval_overview(conversation_id: str | None = None, db: Session = Depends(get_db)):
    return overview(db, conversation_id=conversation_id)


@router.get("/llm")
def eval_llm(conversation_id: str | None = None, db: Session = Depends(get_db)):
    return llm_metrics(db, conversation_id=conversation_id)


@router.get("/retrieval")
def eval_retrieval(conversation_id: str | None = None, db: Session = Depends(get_db)):
    return retrieval_metrics(db, conversation_id=conversation_id)


@router.get("/compression")
def eval_compression(conversation_id: str | None = None, db: Session = Depends(get_db)):
    return compression_metrics(db, conversation_id=conversation_id)


@router.get("/quality")
def eval_quality(conversation_id: str | None = None, db: Session = Depends(get_db)):
    return quality_metrics(db, conversation_id=conversation_id)
