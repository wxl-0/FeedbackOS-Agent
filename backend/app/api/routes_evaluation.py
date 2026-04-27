from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.evaluation_service import compression_metrics, llm_metrics, overview, quality_metrics, retrieval_metrics

router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])


@router.get("/overview")
def eval_overview(db: Session = Depends(get_db)):
    return overview(db)


@router.get("/llm")
def eval_llm(db: Session = Depends(get_db)):
    return llm_metrics(db)


@router.get("/retrieval")
def eval_retrieval(db: Session = Depends(get_db)):
    return retrieval_metrics(db)


@router.get("/compression")
def eval_compression(db: Session = Depends(get_db)):
    return compression_metrics(db)


@router.get("/quality")
def eval_quality(db: Session = Depends(get_db)):
    return quality_metrics(db)

