from typing import TypedDict, Optional, List, Dict, Any


class EmailClassificationState(TypedDict):
    email_id: int
    sender: str
    recipient: str
    subject: str
    body: str

    # Context / Precedents
    similar_examples: Optional[List[Dict[str, Any]]]

    # AI Classification Output
    ai_category: Optional[str]
    confidence: Optional[float]
    reasoning: Optional[str]

    # Human-in-the-Loop Verification
    human_verified: bool
    human_decision: Optional[str]  # "YES" or "NO"
    human_category: Optional[str]  # Required if "NO"
    human_feedback: Optional[str]
    verified_by: Optional[str]

    # Final Result
    final_category: Optional[str]
    verification_status: str  # "pending", "approved", "corrected"
    db_updated: bool
