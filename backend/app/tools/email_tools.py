from typing import Optional, Dict, Any
from langchain_core.tools import tool
from backend.app.database.connection import SessionLocal
from backend.app.database.repository import EmailRepository


@tool
def get_email(email_id: int) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        repo = EmailRepository(db)
        email = repo.get_email_by_id(email_id)
        if not email:
            return {"error": f"Email with ID {email_id} not found."}
        return email.to_dict()
    finally:
        db.close()


@tool
def update_email_classification(
    email_id: int,
    category: str,
    confidence: float,
    verification_status: str = "pending",
    reasoning: str = ""
) -> Dict[str, Any]:
    """
    Update the classification results of an email in NeonDB.
    Sets ai_category, ai_confidence, classification_reason, and verification_status.
    """
    db = SessionLocal()
    try:
        repo = EmailRepository(db)
        email = repo.update_ai_classification(
            email_id=email_id,
            category=category,
            confidence=confidence,
            reasoning=reasoning
        )
        if not email:
            return {"error": f"Email with ID {email_id} not found."}
        return {"success": True, "email_id": email.id, "ai_category": email.ai_category, "status": email.verification_status}
    finally:
        db.close()


@tool
def get_classification_history(email_id: int) -> Dict[str, Any]:
    """
    Retrieve the classification and verification history of an email.
    Returns AI category, AI confidence, reasoning, human category, human decision, and verification timestamp.
    """
    db = SessionLocal()
    try:
        repo = EmailRepository(db)
        email = repo.get_email_by_id(email_id)
        if not email:
            return {"error": f"Email with ID {email_id} not found."}
        return {
            "email_id": email.id,
            "ai_category": email.ai_category,
            "ai_confidence": email.ai_confidence,
            "ai_reasoning": email.classification_reason,
            "verified_category": email.verified_category,
            "verification_status": email.verification_status,
            "human_feedback": email.human_feedback,
            "verified_by": email.verified_by,
            "verified_at": email.verified_at.isoformat() if email.verified_at else None,
        }
    finally:
        db.close()
