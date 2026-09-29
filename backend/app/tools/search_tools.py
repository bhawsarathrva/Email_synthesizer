from typing import List, Dict, Any
from langchain_core.tools import tool
from backend.app.database.connection import SessionLocal
from backend.app.database.repository import EmailRepository


@tool
def search_emails(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search emails in NeonDB matching a query term in subject, body, or sender.
    Example: 'Search emails related to salary'
    """
    db = SessionLocal()
    try:
        repo = EmailRepository(db)
        emails = repo.search_emails(query, limit=limit)
        return [e.to_dict() for e in emails]
    finally:
        db.close()


@tool
def find_similar_emails(email_id: int, limit: int = 3) -> List[Dict[str, Any]]:
    """
    Find previously verified emails that are contextually similar to the specified email.
    Provides verified category precedents (Payroll, Benefits, or Tax) to inform classification.
    """
    db = SessionLocal()
    try:
        repo = EmailRepository(db)
        emails = repo.find_similar_emails(email_id, limit=limit)
        return [
            {
                "id": e.id,
                "subject": e.subject,
                "category": e.verified_category or e.ai_category,
                "verification_status": e.verification_status,
                "reasoning": e.classification_reason
            }
            for e in emails
        ]
    finally:
        db.close()
