import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database.connection import get_db
from backend.app.database.repository import EmailRepository
from backend.app.schemas.email import StatisticsResponse, EvaluationResponse

router = APIRouter(tags=["Statistics & Evaluation"])
logger = logging.getLogger("email_agent.api.statistics")


@router.get("/statistics", response_model=StatisticsResponse)
def get_statistics(db: Session = Depends(get_db)):
    """
    Retrieve real-time aggregate statistics on email counts,
    category breakdowns, and verification statuses.
    """
    repo = EmailRepository(db)
    return repo.get_email_statistics()


@router.get("/evaluation", response_model=EvaluationResponse)
def get_evaluation(db: Session = Depends(get_db)):
    """
    Calculate evaluation metrics (Accuracy, Precision, Recall, F1-Score)
    for Payroll, Benefits, and Tax by comparing AI predictions against human decisions.
    Only human-verified emails are included in the evaluation.
    """
    repo = EmailRepository(db)
    return repo.get_evaluation_metrics()
