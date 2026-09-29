import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.database.connection import get_db
from backend.app.database.repository import EmailRepository
from backend.app.schemas.email import EmailResponse, EmailListResponse

router = APIRouter(prefix="/emails", tags=["Emails"])
logger = logging.getLogger("email_agent.api.emails")


@router.get("", response_model=EmailListResponse)
def get_emails(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category (Payroll, Benefits, Tax)"),
    status: Optional[str] = Query(None, description="Filter by status (pending, approved, corrected)"),
    search: Optional[str] = Query(None, description="Search query across subject, body, sender"),
    db: Session = Depends(get_db)
):
    """Retrieve paginated emails with optional category, status, and search filters."""
    repo = EmailRepository(db)
    emails, total = repo.get_emails(
        page=page,
        limit=limit,
        category=category,
        status=status,
        search_query=search
    )
    return EmailListResponse(
        emails=[EmailResponse(**e.to_dict()) for e in emails],
        total=total,
        page=page,
        limit=limit
    )


@router.get("/{email_id}", response_model=EmailResponse)
def get_single_email(
    email_id: int,
    db: Session = Depends(get_db)
):
    """Retrieve details for a specific email by ID."""
    repo = EmailRepository(db)
    email = repo.get_email_by_id(email_id)
    if not email:
        raise HTTPException(status_code=404, detail=f"Email with ID {email_id} not found.")
    return EmailResponse(**email.to_dict())
