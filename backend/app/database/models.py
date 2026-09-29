from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, DateTime
from backend.app.database.connection import Base


class Email(Base):
    __tablename__ = "Email_data"

    id = Column(Integer, primary_key=True, index=True)
    
    # Original columns in database
    To_email = Column("To", String(255), nullable=True)
    From_email = Column("From", String(255), nullable=True)
    Subject_text = Column("Subject", String(300), nullable=True)
    Body_text = Column("Body", Text, nullable=True)
    Category_legacy = Column("Category", String(255), nullable=True)
    Verified_legacy = Column("Verified", String(255), nullable=True)

    # Classification & Verification Columns
    ai_category = Column(String(50), nullable=True, index=True)
    ai_confidence = Column(Float, nullable=True)
    classification_reason = Column(Text, nullable=True)

    verified_category = Column(String(50), nullable=True, index=True)
    verification_status = Column(String(50), default="pending", index=True)
    human_feedback = Column(Text, nullable=True)
    verified_by = Column(String(100), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    received_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=True)

    # Friendly property aliases
    @property
    def sender(self) -> str:
        return self.From_email or ""

    @sender.setter
    def sender(self, val: str):
        self.From_email = val

    @property
    def recipient(self) -> str:
        return self.To_email or ""

    @recipient.setter
    def recipient(self, val: str):
        self.To_email = val

    @property
    def subject(self) -> str:
        return self.Subject_text or ""

    @subject.setter
    def subject(self, val: str):
        self.Subject_text = val

    @property
    def body(self) -> str:
        return self.Body_text or ""

    @body.setter
    def body(self, val: str):
        self.Body_text = val

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "sender": self.sender,
            "recipient": self.recipient,
            "subject": self.subject,
            "body": self.body,
            "ai_category": self.ai_category or self.Category_legacy,
            "ai_confidence": self.ai_confidence,
            "classification_reason": self.classification_reason,
            "verified_category": self.verified_category or self.Category_legacy,
            "verification_status": self.verification_status or "pending",
            "human_feedback": self.human_feedback,
            "verified_by": self.verified_by,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "received_at": self.received_at.isoformat() if self.received_at else None,
        }
