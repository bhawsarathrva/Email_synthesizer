from typing import Dict, Any
from langchain_core.tools import tool
from backend.app.database.connection import SessionLocal
from backend.app.database.repository import EmailRepository


@tool
def get_email_statistics() -> Dict[str, Any]:
    """
    Retrieve real-time email classification statistics from NeonDB:
    - Total Emails
    - Payroll Emails
    - Benefits Emails
    - Tax Emails
    - Pending Verification
    - Approved
    - Corrected
    """
    db = SessionLocal()
    try:
        repo = EmailRepository(db)
        return repo.get_email_statistics()
    finally:
        db.close()
