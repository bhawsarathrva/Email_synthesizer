from datetime import datetime
from typing import Optional, List, Literal, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class EmailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sender: str
    recipient: str
    subject: str
    body: str
    ai_category: Optional[str] = None
    ai_confidence: Optional[float] = None
    classification_reason: Optional[str] = None
    verified_category: Optional[str] = None
    verification_status: str = "pending"
    human_feedback: Optional[str] = None
    verified_by: Optional[str] = None
    verified_at: Optional[str] = None
    received_at: Optional[str] = None


class EmailListResponse(BaseModel):
    emails: List[EmailResponse]
    total: int
    page: int
    limit: int


class VerificationRequest(BaseModel):
    decision: Literal["YES", "NO"] = Field(
        ...,
        description="Human reviewer decision: 'YES' to accept AI category, 'NO' to correct it."
    )
    correct_category: Optional[Literal["Payroll", "Benefits", "Tax"]] = Field(
        default=None,
        description="Mandatory if decision is 'NO'. Must be one of 'Payroll', 'Benefits', or 'Tax'."
    )
    feedback: Optional[str] = Field(
        default=None,
        description="Optional human feedback or reason for correction/approval."
    )
    verified_by: Optional[str] = Field(
        default="human_reviewer",
        description="Identifier of the reviewer."
    )


class ClassifyResponse(BaseModel):
    email_id: int
    category: Literal["Payroll", "Benefits", "Tax"]
    confidence: float
    reasoning: str
    requires_verification: bool = True


class CategoryMetric(BaseModel):
    precision: float
    recall: float
    f1: float
    support: int


class EvaluationResponse(BaseModel):
    verified_count: int
    accuracy: float
    payroll: CategoryMetric
    benefits: CategoryMetric
    tax: CategoryMetric


class StatisticsResponse(BaseModel):
    total_emails: int
    payroll_emails: int
    benefits_emails: int
    tax_emails: int
    pending_verification: int
    approved: int
    corrected: int
