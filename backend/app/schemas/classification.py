from typing import Literal
from pydantic import BaseModel, Field


class ClassificationResult(BaseModel):
    category: Literal["Payroll", "Benefits", "Tax"] = Field(
        ...,
        description="The classified category for the email. Must be exactly one of: Payroll, Benefits, Tax."
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 and 1.0 representing certainty."
    )
    reasoning: str = Field(
        ...,
        description="Clear, concise explanation for why the email belongs to this category based on subject and body."
    )
