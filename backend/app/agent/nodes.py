import logging
from typing import Dict, Any
from langgraph.types import interrupt
from backend.app.agent.state import EmailClassificationState
from backend.app.database.connection import SessionLocal
from backend.app.database.repository import EmailRepository
from backend.app.agent.classifier import classify_email_content

logger = logging.getLogger("email_agent.nodes")


def fetch_email_node(state: EmailClassificationState) -> Dict[str, Any]:
    """Node 1: Fetches the email from NeonDB and looks up similar verified emails."""
    email_id = state["email_id"]
    db = SessionLocal()
    try:
        repo = EmailRepository(db)
        email = repo.get_email_by_id(email_id)
        if not email:
            raise ValueError(f"Email with ID {email_id} not found in database.")

        similar = repo.find_similar_emails(email_id, limit=3)
        similar_data = [
            {"subject": s.subject, "category": s.verified_category or s.ai_category}
            for s in similar
        ]

        logger.info(f"Fetched email {email_id}: Subject='{email.subject}' | Similar count={len(similar_data)}")
        return {
            "sender": email.sender,
            "recipient": email.recipient,
            "subject": email.subject,
            "body": email.body,
            "similar_examples": similar_data,
        }
    finally:
        db.close()


def classify_email_node(state: EmailClassificationState) -> Dict[str, Any]:
    """Node 2: Runs AI classification on the subject and body using structured LLM output."""
    result = classify_email_content(
        subject=state["subject"],
        body=state["body"],
        sender=state.get("sender", ""),
        recipient=state.get("recipient", ""),
        similar_examples=state.get("similar_examples", [])
    )

    logger.info(f"Classified email {state['email_id']}: {result.category} (Confidence: {result.confidence})")

    # Persist the initial AI classification into the database
    db = SessionLocal()
    try:
        repo = EmailRepository(db)
        repo.update_ai_classification(
            email_id=state["email_id"],
            category=result.category,
            confidence=result.confidence,
            reasoning=result.reasoning
        )
    finally:
        db.close()

    return {
        "ai_category": result.category,
        "confidence": result.confidence,
        "reasoning": result.reasoning
    }


def prepare_verification_node(state: EmailClassificationState) -> Dict[str, Any]:
    """Node 3: Formats and prepares the verification prompt payload."""
    return {
        "human_verified": False,
        "verification_status": "pending"
    }


def human_verification_node(state: EmailClassificationState) -> Dict[str, Any]:
    """
    Node 4: Human-in-the-Loop Interrupt.
    Pauses graph execution using LangGraph's interrupt() mechanism.
    Resumes when human provides a decision ('YES' or 'NO').
    """
    interrupt_payload = {
        "email_id": state["email_id"],
        "subject": state["subject"],
        "body": state["body"],
        "ai_category": state["ai_category"],
        "confidence": state["confidence"],
        "reasoning": state["reasoning"],
        "message": f"AI classified this email as '{state['ai_category']}' with {int((state['confidence'] or 0.9)*100)}% confidence. Please verify."
    }

    logger.info(f"Triggering LangGraph interrupt for email {state['email_id']}...")
    # This call pauses execution until resumed with Command(resume=...)
    human_input = interrupt(interrupt_payload)

    logger.info(f"Resumed from interrupt with human response: {human_input}")
    decision = human_input.get("decision", "YES").upper()
    correct_category = human_input.get("correct_category")
    feedback = human_input.get("feedback")
    verified_by = human_input.get("verified_by", "human_reviewer")

    return {
        "human_verified": True,
        "human_decision": decision,
        "human_category": correct_category,
        "human_feedback": feedback,
        "verified_by": verified_by
    }


def human_correction_node(state: EmailClassificationState) -> Dict[str, Any]:
    """Node 5a: Applied when human rejects AI prediction ('NO'). Sets the corrected category."""
    human_cat = state.get("human_category")
    logger.info(f"Human correction applied for email {state['email_id']}: Corrected to '{human_cat}'")
    return {
        "final_category": human_cat,
        "verification_status": "corrected"
    }


def determine_final_category_node(state: EmailClassificationState) -> Dict[str, Any]:
    """Node 5: Resolves the final category based on human decision."""
    decision = state.get("human_decision", "YES")
    if decision == "YES":
        final_cat = state["ai_category"]
        status = "approved"
    else:
        final_cat = state.get("human_category") or state["ai_category"]
        status = "corrected"

    logger.info(f"Final category for email {state['email_id']} determined as '{final_cat}' with status '{status}'")
    return {
        "final_category": final_cat,
        "verification_status": status
    }


def update_database_node(state: EmailClassificationState) -> Dict[str, Any]:
    """Node 6: Stores verified category and status in NeonDB while preserving AI prediction."""
    email_id = state["email_id"]
    db = SessionLocal()
    try:
        repo = EmailRepository(db)
        repo.record_human_verification(
            email_id=email_id,
            decision=state.get("human_decision", "YES"),
            correct_category=state.get("human_category"),
            feedback=state.get("human_feedback"),
            verified_by=state.get("verified_by", "human_reviewer")
        )
        logger.info(f"Successfully updated NeonDB for email {email_id}!")
        return {"db_updated": True}
    finally:
        db.close()
