import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from langgraph.types import Command
from backend.app.database.connection import get_db
from backend.app.database.repository import EmailRepository
from backend.app.schemas.email import VerificationRequest, ClassifyResponse, EmailResponse
from backend.app.agent.graph import email_agent_graph

router = APIRouter(prefix="/emails", tags=["Classification & Verification"])
logger = logging.getLogger("email_agent.api.verification")


@router.post("/{email_id}/classify", response_model=ClassifyResponse)
def classify_email_endpoint(
    email_id: int,
    db: Session = Depends(get_db)
):
    """
    Triggers AI Classification for the specified email.
    The LangGraph workflow runs through fetch -> classify -> prepare_verification,
    and pauses at human_verification (HITL interrupt), waiting for human review.
    """
    repo = EmailRepository(db)
    email = repo.get_email_by_id(email_id)
    if not email:
        raise HTTPException(status_code=404, detail=f"Email with ID {email_id} not found.")

    thread_config = {"configurable": {"thread_id": f"email_{email_id}"}}
    initial_state = {"email_id": email_id}

    logger.info(f"Initiating agent workflow for email {email_id}...")
    try:
        # Run graph until interrupt
        email_agent_graph.invoke(initial_state, config=thread_config)
        state_snapshot = email_agent_graph.get_state(thread_config)

        if state_snapshot.tasks and state_snapshot.tasks[0].interrupts:
            interrupt_val = state_snapshot.tasks[0].interrupts[0].value
            return ClassifyResponse(
                email_id=email_id,
                category=interrupt_val["ai_category"],
                confidence=interrupt_val["confidence"],
                reasoning=interrupt_val["reasoning"],
                requires_verification=True
            )
        else:
            # If for any reason graph ran through or had existing values
            cat = state_snapshot.values.get("ai_category") or email.ai_category or "Payroll"
            conf = state_snapshot.values.get("confidence") or email.ai_confidence or 0.95
            reason = state_snapshot.values.get("reasoning") or email.classification_reason or "Classified by agent."
            return ClassifyResponse(
                email_id=email_id,
                category=cat,
                confidence=conf,
                reasoning=reason,
                requires_verification=True
            )

    except Exception as e:
        logger.error(f"Error during agent classification: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Classification workflow error: {str(e)}")


@router.post("/{email_id}/verify", response_model=EmailResponse)
def verify_email_endpoint(
    email_id: int,
    req: VerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Submits human verification decision ('YES' or 'NO').
    Resumes the LangGraph interrupt and persists the final result to NeonDB.
    """
    repo = EmailRepository(db)
    email = repo.get_email_by_id(email_id)
    if not email:
        raise HTTPException(status_code=404, detail=f"Email with ID {email_id} not found.")

    if req.decision == "NO" and not req.correct_category:
        raise HTTPException(
            status_code=400,
            detail="When decision is 'NO', 'correct_category' must be provided ('Payroll', 'Benefits', or 'Tax')."
        )

    thread_config = {"configurable": {"thread_id": f"email_{email_id}"}}
    state_snapshot = email_agent_graph.get_state(thread_config)

    resume_payload = {
        "decision": req.decision,
        "correct_category": req.correct_category,
        "feedback": req.feedback,
        "verified_by": req.verified_by or "human_reviewer"
    }

    try:
        # Check if the thread is currently paused in an interrupt
        if state_snapshot.next and "human_verification" in state_snapshot.next:
            logger.info(f"Resuming LangGraph interrupt for thread email_{email_id}...")
            email_agent_graph.invoke(Command(resume=resume_payload), config=thread_config)
        else:
            # If graph is not paused at interrupt (e.g. direct verify call), persist directly via repository
            logger.info(f"Directly recording human verification for email {email_id}...")
            repo.record_human_verification(
                email_id=email_id,
                decision=req.decision,
                correct_category=req.correct_category,
                feedback=req.feedback,
                verified_by=req.verified_by or "human_reviewer"
            )

        # Refresh and return updated email
        db.expire_all()
        updated_email = repo.get_email_by_id(email_id)
        return EmailResponse(**updated_email.to_dict())

    except Exception as e:
        logger.error(f"Error during human verification resume: {e}", exc_info=True)
        # Fallback to direct DB update to guarantee data consistency
        repo.record_human_verification(
            email_id=email_id,
            decision=req.decision,
            correct_category=req.correct_category,
            feedback=req.feedback,
            verified_by=req.verified_by or "human_reviewer"
        )
        db.expire_all()
        updated_email = repo.get_email_by_id(email_id)
        return EmailResponse(**updated_email.to_dict())
